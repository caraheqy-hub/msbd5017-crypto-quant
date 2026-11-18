//go:build wasip1

// Parameterised indicator strategy for strategy search on the Argo platform.
// One WASM handles many variants selected by the strategy YAML "kind" field:
//   macd | ma | ema | rsi | williams | psy | range_filter
// Each variant is long-only: buy on BUY_LONG, close on SELL_SHORT.
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"math"
	"strconv"

	"github.com/knqyf263/go-plugin/types/known/emptypb"
	"github.com/rxtech-lab/argo-trading/pkg/strategy"
)

type Config struct {
	Kind       string  `json:"kind"`
	Fast       int     `json:"fast"`
	Slow       int     `json:"slow"`
	Signal     int     `json:"signal"`
	Period     int     `json:"period"`
	Oversold   float64 `json:"oversold"`
	Overbought float64 `json:"overbought"`
	Multiplier float64 `json:"multiplier"`
	Upper      float64 `json:"upper"`
	Lower      float64 `json:"lower"`
	Delay      bool    `json:"delay"`
}

type SearchStrategy struct {
	cfg     Config
	indType strategy.IndicatorType
}

func main() {}

func init() {
	strategy.RegisterTradingStrategy(&SearchStrategy{})
}

func (s *SearchStrategy) Initialize(_ context.Context, req *strategy.InitializeRequest) (*emptypb.Empty, error) {
	s.cfg = Config{Kind: "macd", Fast: 12, Slow: 26, Signal: 9, Period: 14,
		Oversold: 30, Overbought: 70, Multiplier: 3, Upper: 75, Lower: 25}
	if req.Config != "" {
		_ = json.Unmarshal([]byte(req.Config), &s.cfg)
	}

	api := strategy.NewStrategyApi()
	var cfgStr string
	switch s.cfg.Kind {
	case "macd":
		s.indType = strategy.IndicatorType_INDICATOR_MACD
		cfgStr = fmt.Sprintf("[%d,%d,%d]", s.cfg.Fast, s.cfg.Slow, s.cfg.Signal)
	case "ma":
		s.indType = strategy.IndicatorType_INDICATOR_MA
		cfgStr = fmt.Sprintf("[%d]", s.cfg.Period)
	case "ema":
		s.indType = strategy.IndicatorType_INDICATOR_EMA
		cfgStr = fmt.Sprintf("[%d]", s.cfg.Period)
	case "rsi":
		s.indType = strategy.IndicatorType_INDICATOR_RSI
		cfgStr = fmt.Sprintf("[%d,%.2f,%.2f]", s.cfg.Period, s.cfg.Oversold, s.cfg.Overbought)
	case "williams":
		s.indType = strategy.IndicatorType_INDICATOR_WILLIAMS_R
		cfgStr = fmt.Sprintf("[%d,%.2f,%.2f]", s.cfg.Period, s.cfg.Overbought, s.cfg.Oversold)
	case "psy":
		s.indType = strategy.IndicatorType_INDICATOR_PSY
		cfgStr = fmt.Sprintf("[%d,%.2f,%.2f]", s.cfg.Period, s.cfg.Upper, s.cfg.Lower)
	case "range_filter":
		s.indType = strategy.IndicatorType_INDICATOR_RANGE_FILTER
		cfgStr = fmt.Sprintf("[%d,%.2f]", s.cfg.Period, s.cfg.Multiplier)
	default:
		return nil, fmt.Errorf("unknown kind %q", s.cfg.Kind)
	}

	_, err := api.ConfigureIndicator(context.Background(), &strategy.ConfigureRequest{
		IndicatorType: s.indType,
		Config:        cfgStr,
	})
	return &emptypb.Empty{}, err
}

func (s *SearchStrategy) ProcessData(ctx context.Context, req *strategy.ProcessDataRequest) (*emptypb.Empty, error) {
	data := req.Data
	api := strategy.NewStrategyApi()
	key := "pos_" + data.Symbol
	prev, err := api.GetCache(ctx, &strategy.GetRequest{Key: key})
	inPos := err == nil && prev.Value == "1"

	sig, err := api.GetSignal(ctx, &strategy.GetSignalRequest{
		IndicatorType: s.indType,
		MarketData:    data,
	})
	if err != nil {
		return nil, err
	}

	// actType is normally the current bar's signal. With Delay it is the
	// previous bar's signal, so the decision uses only completed bars and the
	// fill happens on the following bar (removes same-bar look-ahead).
	actType := sig.Type
	if s.cfg.Delay {
		sigKey := "sigtype_" + data.Symbol

		// No prior signal yet: do not trade on the current bar's signal, otherwise
		// the first trade reintroduces same-bar look-ahead.
		actType = strategy.SignalType_SIGNAL_TYPE_NO_ACTION

		if p, e := api.GetCache(ctx, &strategy.GetRequest{Key: sigKey}); e == nil && p != nil && p.Value != "" {
			if n, e2 := strconv.Atoi(p.Value); e2 == nil {
				actType = strategy.SignalType(n)
			}
		}

		_, _ = api.SetCache(ctx, &strategy.SetRequest{Key: sigKey, Value: strconv.Itoa(int(sig.Type))})
	}

	switch actType {
	case strategy.SignalType_SIGNAL_TYPE_BUY_LONG:
		if inPos {
			return &emptypb.Empty{}, nil
		}
		acct, err := api.GetAccountInfo(ctx, &emptypb.Empty{})
		if err != nil {
			return nil, err
		}
		qty := math.Floor(acct.BuyingPower*0.45/data.Close*100) / 100
		if qty <= 0 {
			return &emptypb.Empty{}, nil
		}
		_, err = api.PlaceOrder(ctx, &strategy.ExecuteOrder{
			Symbol: data.Symbol, Side: strategy.PurchaseType_PURCHASE_TYPE_BUY,
			OrderType: strategy.OrderType_ORDER_TYPE_MARKET,
			Quantity:  qty, Price: data.Close, StrategyName: "Search",
			Reason: &strategy.Reason{Reason: "signal", Message: s.cfg.Kind + " buy"},
		})
		if err != nil {
			return nil, err
		}
		_, _ = api.SetCache(ctx, &strategy.SetRequest{Key: key, Value: "1"})
	case strategy.SignalType_SIGNAL_TYPE_SELL_SHORT:
		if !inPos {
			return &emptypb.Empty{}, nil
		}
		pos, err := api.GetPosition(ctx, &strategy.GetPositionRequest{Symbol: data.Symbol})
		if err == nil && pos != nil && pos.Quantity > 0 {
			_, err = api.PlaceOrder(ctx, &strategy.ExecuteOrder{
				Symbol: data.Symbol, Side: strategy.PurchaseType_PURCHASE_TYPE_SELL,
				OrderType: strategy.OrderType_ORDER_TYPE_MARKET,
				Quantity:  pos.Quantity, Price: data.Close, StrategyName: "Search",
				Reason: &strategy.Reason{Reason: "signal", Message: s.cfg.Kind + " sell"},
			})
			if err != nil {
				return nil, err
			}
		}
		_, _ = api.SetCache(ctx, &strategy.SetRequest{Key: key, Value: "0"})
	}
	return &emptypb.Empty{}, nil
}

func (s *SearchStrategy) Name(_ context.Context, _ *strategy.NameRequest) (*strategy.NameResponse, error) {
	return &strategy.NameResponse{Name: "Search"}, nil
}

func (s *SearchStrategy) GetConfigSchema(_ context.Context, _ *strategy.GetConfigSchemaRequest) (*strategy.GetConfigSchemaResponse, error) {
	return &strategy.GetConfigSchemaResponse{Schema: ""}, nil
}

func (s *SearchStrategy) GetDescription(_ context.Context, _ *strategy.GetDescriptionRequest) (*strategy.GetDescriptionResponse, error) {
	return &strategy.GetDescriptionResponse{Description: "Parameterised indicator strategy for strategy search"}, nil
}

func (s *SearchStrategy) GetIdentifier(_ context.Context, _ *strategy.GetIdentifierRequest) (*strategy.GetIdentifierResponse, error) {
	return &strategy.GetIdentifierResponse{Identifier: "com.argo-trading.examples.search"}, nil
}

//+------------------------------------------------------------------+
//|                                                    ea course.mq4 |
//|                        Copyright 2020, MetaQuotes Software Corp. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2020, MetaQuotes Software Corp."
#property link      "https://www.mql5.com"
#property version   "1.00"
#property strict
input double   LotSize             = 0.01;    // Lot Size
input double   TP                  = 6.00;   // Take Profit (pips)
input double   SL                  = 30.00;   // Stop Loss (pips)
input int      MaxOrders           = 16;      // Max Orders
input double   LotsMultiplier      = 1.369;   // Lots Multiplier
input double   MinOrderDistance    = 10.00;   // Min Order Distance
input bool     AllowBuy            = true;    // Allow Buy
input bool     AllowSell           = true;    // Allow Sell
input bool     AllowOppositeOrder  = true;    // Allow Opposite Order
input int      EAMagicNo           = 12345;   // EA Magic No
input string   EAComment           = "";      // EA Comment

double dGLotSize;
string sGComments;
//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
//---
    // Check the dll allowed
    if (!IsDllsAllowed())
    {
      Comment("DLL is not allowed. Go to menu Tools - Options - Experts Tab to fixed it");
      return (INIT_FAILED);
    }
    
    // Check the Expert Enabled
    if (!IsExpertEnabled())
    {
      Comment("Expert is not enabled");
      return (INIT_FAILED);
    }
    
    // Check the account balance
    if (AccountBalance()<=0)
    {
      Comment("Balance is 0");
      return (INIT_FAILED);
    }
    
    dGLotSize = dFAdjustLotSize(LotSize);
    
    OnTick();
    
//---
   return(INIT_SUCCEEDED);
  }
  
double dFAdjustLotSize(double dLots)
  {
    double dLotStep = MarketInfo(NULL, MODE_LOTSTEP),
           dMinLot  = MarketInfo(NULL, MODE_MINLOT),
           dMaxLot  = MarketInfo(NULL, MODE_MAXLOT);
           
    double dLotSize = NormalizeDouble(dLots/dLotStep,0)*dLotStep;
    
    if (dLotSize < dMinLot)
      return (dMinLot);
    else if (dLotSize > dMaxLot)
      return (dMaxLot);
    else
      return (dLotSize);
  }

void vFOpenOrder()
  {
    bool  bAllowBuy = AllowBuy,
          bAllowSell = AllowSell;
    int iTicket;
    
    // Continue check for every new bar
    static int iLastBar=0;
    if (iLastBar==Bars)
      return;
    iLastBar = Bars;
    
    //Check Existing Order Buy
    if (iFCheckOrdersPart(OP_BUY,EAMagicNo)==0)
    {
      if (iFCheckOrdersPart(OP_SELL,EAMagicNo)>=1)
      {
        if (bAllowBuy && AllowOppositeOrder)
          bAllowBuy = true;
        else
          bAllowBuy = false;
      }
      
      // Check buy condition
      if (bAllowBuy && bFIsOverSold() && bFCandleBullish() && bFCheckFreeMargin(NULL,dGLotSize,OP_BUY))
      {
        iTicket=OrderSend(NULL,OP_BUY,dGLotSize,Ask,5,0,0,EAComment,EAMagicNo,0,clrDodgerBlue);
        if (iTicket<0)
          Print("Open Buy Error Code : ", GetLastError());
      }
    }
    
    
    //Check Existing Order Sell
    if (iFCheckOrdersPart(OP_SELL,EAMagicNo)==0)
    {
      if (iFCheckOrdersPart(OP_BUY,EAMagicNo)>=1)
      {
        if (bAllowSell && AllowOppositeOrder)
          bAllowSell = true;
        else
          bAllowSell = false;
      }
      
      // Check Sell Condition
      if (bAllowSell && bFIsOverBought() && bFCandleBearish() && bFCheckFreeMargin(NULL,dGLotSize,OP_SELL))
      {
        iTicket=OrderSend(NULL,OP_SELL,dGLotSize,Bid,5,0,0,EAComment,EAMagicNo,0,clrDeepPink);
        if (iTicket<0)
          Print("Open Sell Error Code : ", GetLastError());
      }
    }
    
  }
  
int iFCheckOrdersPart(int iCmd, int iMagicNo)
  {
    int i, iOrder=0, iTotalOrders=OrdersTotal();
    
    if (iTotalOrders>0)
    {
      for (i=1;i<=iTotalOrders;i++)
      {
        if (OrderSelect(i-1,SELECT_BY_POS,MODE_TRADES)==true)
        {
          if (OrderSymbol()==Symbol() && OrderMagicNumber()==iMagicNo && OrderType()==iCmd)
            iOrder+=1;
        }
      }
    }
    return(iOrder);
  }
  
// Check if Over Bought
bool bFIsOverBought()
  {
    double dDeMaker;
    
    dDeMaker = iDeMarker(NULL,0,10,1);
    
    if (dDeMaker >= 0.9)
      return(true);
    else
      return(false);
  }

// Check if Over Sold
bool bFIsOverSold()
  {
    double dDeMaker;
    
    dDeMaker = iDeMarker(NULL,0,10,1);
    
    if (dDeMaker <= 0.1)
      return(true);
    else
      return(false);
  }

// Check Candle Bullish
bool bFCandleBullish()
  {
    double dOpen  = iOpen(NULL,0,1),
           dClose = iClose(NULL,0,1);
    
    return(dOpen<dClose);
  }

// Check Candle Bearish
bool bFCandleBearish()
  {
    double dOpen  = iOpen(NULL,0,1),
           dClose = iClose(NULL,0,1);
    
    return(dOpen>dClose);
  }

// Check Free Margin
bool bFCheckFreeMargin(string sSymbol, double dLots, int iCmd)
  {
    double dFreeMargin = AccountFreeMarginCheck(sSymbol,iCmd,dLots);
    
    if (dFreeMargin<0)
    {
      string sOperation=(iCmd==OP_BUY)?"Buy":"Sell";
      Print("Not enough money for ", sOperation,"  ", dLots," ",sSymbol, " Error Code=", GetLastError());
      return(false);
    }
    
    // Check is successful
    return(true);
  }
  
int iFDigit()
  {
    if (Digits()==3 || Digits()==5)
      return(10);
    else
      return(1);
  }
  
double dFGetAvgLotSize(int iOrder)
  {
    int i;
    double dLot=dGLotSize;
    
    for (i=0; i<=iOrder-1; i++)
    {
      dLot=dLot*LotsMultiplier;
    }
    
    return(dFAdjustLotSize(dLot));
  }

double dFHighestPrice(int iCmd, int iCmdPending1, int iCmdPending2, int iEAMagicNo, double dPrice)
  {
    int i;
    double dMaxPrice=dPrice;
    
    for (i=0; i<OrdersTotal(); i++)
    {
      if (OrderSelect(i,SELECT_BY_POS)==true)
      {
        if (OrderSymbol()==Symbol() && OrderMagicNumber()==iEAMagicNo &&
           (OrderType()==iCmd || OrderType()==iCmdPending1 || OrderType()==iCmdPending2))
          dMaxPrice=MathMax(dMaxPrice,OrderOpenPrice());
      }
    }
    
    return(dMaxPrice);
  }
  
double dFLowestPrice(int iCmd, int iCmdPending1, int iCmdPending2, int iEAMagicNo, double dPrice)
  {
    int i;
    double dMinPrice=dPrice;
    
    for(i=0; i<OrdersTotal(); i++)
    {
      if (OrderSelect(i,SELECT_BY_POS)==true)
      {
        if (OrderSymbol()==Symbol() && OrderMagicNumber()==iEAMagicNo &&
           (OrderType()==iCmd || OrderType()==iCmdPending1 || OrderType()==iCmdPending2))
          dMinPrice=MathMin(dMinPrice,OrderOpenPrice());
      }
    }
    
    return(dMinPrice);
  }

void vFHandleAvg()
  {
    double dOrderDist, dStopLevel=MarketInfo(NULL,MODE_STOPLEVEL);
    int iTicket;
    
    static int iLastBar=0;
    if (iLastBar==Bars)
      return;
    iLastBar=Bars;
    
    dOrderDist=MinOrderDistance*iFDigit();
    dOrderDist=MathMax(dOrderDist,dStopLevel)*Point;
    
    // Open Buy Avg
    if (iFCheckOrdersPart(OP_BUY,EAMagicNo)>0)
    {
      if (iFCheckOrdersPart(OP_BUY,EAMagicNo)<MaxOrders && MaxOrders>0)
      {
        if (AllowBuy && dFLowestPrice(OP_BUY,OP_BUYLIMIT,OP_BUYSTOP,EAMagicNo,99999999)-Ask>dOrderDist)
        {
          if (bFCheckFreeMargin(NULL,dFGetAvgLotSize(iFCheckOrdersPart(OP_BUY,EAMagicNo)),OP_BUY))
          {
            iTicket=OrderSend(NULL,OP_BUY,dFGetAvgLotSize(iFCheckOrdersPart(OP_BUY,EAMagicNo)),Ask,5,0,0,EAComment,EAMagicNo,0,clrDodgerBlue);
            
            if (iTicket<0)
              Print ("Open Buy Error Code: ", GetLastError());
          }
        }
      }
    }
    
    // Open Sell Avg
    if (iFCheckOrdersPart(OP_SELL,EAMagicNo)>0)
    {
      if (iFCheckOrdersPart(OP_SELL,EAMagicNo)<MaxOrders && MaxOrders>0)
      {
        if (AllowSell && Bid-dFHighestPrice(OP_SELL,OP_SELLLIMIT,OP_SELLSTOP,EAMagicNo,0)>dOrderDist)
        {
          if (bFCheckFreeMargin(NULL,dFGetAvgLotSize(iFCheckOrdersPart(OP_SELL,EAMagicNo)),OP_SELL))
          {
            iTicket=OrderSend(NULL,OP_SELL,dFGetAvgLotSize(iFCheckOrdersPart(OP_SELL,EAMagicNo)),Bid,5,0,0,EAComment,EAMagicNo,0,clrDeepPink);
            
            if (iTicket<0)
              Print ("Open Sell Error Code: ", GetLastError());
          }
        }
      }
    }
  }

void vFCountBEP(int iCmd)
  {
    int i, iTotalOrders=OrdersTotal();
    double dOrderLots=0, dOrderPrice=0, dBEPPrice=0;
    
    for (i=1; i<=iTotalOrders; i++)
    {
      if (OrderSelect(i-1,SELECT_BY_POS,MODE_TRADES)==true)
      {
        if (OrderSymbol()==Symbol() && OrderMagicNumber()==EAMagicNo && OrderType()==iCmd)
        {
          dOrderLots += OrderLots();
          dOrderPrice += OrderLots() * OrderOpenPrice();
        }
      }
    }
    
    dBEPPrice = dOrderPrice/dOrderLots;
    
    // Create BEP Line
    if (iCmd==OP_BUY)
    {
      if (ObjectFind(0,"BuyAverage")==0)   // if the Buy Average line is exist
        ObjectMove(0,"BuyAverage",0,TimeCurrent(),dBEPPrice);
      else
      {
        //Create the Buy Average Line
        ObjectCreate(0,"BuyAverage",OBJ_HLINE,0,TimeCurrent(),dBEPPrice);
        ObjectSet("BuyAverage",OBJPROP_COLOR,clrLightSkyBlue);
        ObjectSet("BuyAverage",OBJPROP_STYLE,STYLE_DOT);
      }
    }
    else
    {
      if (ObjectFind(0,"SellAverage")==0)   // if the Sell Average line is exist
        ObjectMove(0,"SellAverage",0,TimeCurrent(),dBEPPrice);
      else
      {
        //Create Sell Average Line
        ObjectCreate(0,"SellAverage",OBJ_HLINE,0,TimeCurrent(),dBEPPrice);
        ObjectSet("SellAverage",OBJPROP_COLOR,clrViolet);
        ObjectSet("SellAverage",OBJPROP_STYLE,STYLE_DOT);
      }
    }
  }

// Return the price from line
double dFReturnPrice(string sLine)
  {
    return (ObjectGet(sLine,OBJPROP_PRICE1));
  }
  
void vFHandleSLTP(int iCmd)
  {
    double dTP=TP*iFDigit()*Point,
           dSL=SL*iFDigit()*Point,
           dStopLv=MarketInfo(NULL,MODE_STOPLEVEL),
           dBuyPrice, dSellPrice,
           dBuyOP, dSellOP;
    int i, iTotalOrders=OrdersTotal(), iTicket;
    
    // Create and modify the TakeProfit
    if (dTP>0)
    {
      if (iCmd==OP_BUY)
      {
        if (ObjectFind(0,"BuyAverage")!=0)
          dBuyPrice=dFHighestPrice(OP_BUY,OP_BUYLIMIT,OP_BUYSTOP,EAMagicNo,0);
        else
          dBuyPrice=dFReturnPrice("BuyAverage");
          
        dTP=dBuyPrice+(MathMax(dTP,dStopLv*Point));
        dTP=NormalizeDouble(dTP,Digits);
        
        for (i=1; i<=iTotalOrders; i++)
        {
          if (OrderSelect(i-1,SELECT_BY_POS,MODE_TRADES)==true)
          {
            if (OrderSymbol()==Symbol() && OrderMagicNumber()==EAMagicNo && OrderType()==OP_BUY)
            {
              if (OrderTakeProfit()!=dTP)  // Modify the TakeProfit
              {
                iTicket=OrderModify(OrderTicket(),OrderOpenPrice(),OrderStopLoss(),dTP,0,clrDodgerBlue);
                
                if (iTicket<0)
                  Print("Modify Buy TP Error Code: ", GetLastError());
              }
            }
          }
        }
      }
      else
      {
        if (ObjectFind(0,"SellAverage")!=0)
          dSellPrice=dFLowestPrice(OP_SELL,OP_SELLLIMIT,OP_SELLSTOP,EAMagicNo,99999999);
        else
          dSellPrice=dFReturnPrice("SellAverage");
        
        dTP=dSellPrice-(MathMax(dTP,dStopLv*Point));
        dTP=NormalizeDouble(dTP,Digits);
        
        for (i=1; i<=iTotalOrders; i++)
        {
          if (OrderSelect(i-1,SELECT_BY_POS,MODE_TRADES)==true)
          {
            if (OrderSymbol()==Symbol() && OrderMagicNumber()==EAMagicNo && OrderType()==OP_SELL)
            {
              if (OrderTakeProfit()!=dTP)
              {
                iTicket=OrderModify(OrderTicket(),OrderOpenPrice(),OrderStopLoss(),dTP,0,clrDeepPink);
                
                if (iTicket<0)
                  Print ("Modify Sell TP Error Code: ", GetLastError());
              }
            }
          }
        }
      }
    }
    
    // Create and modify StopLoss
    if (dSL>0)
    {
      if (iCmd==OP_BUY)
      {
        if (iFCheckOrdersPart(OP_BUY,EAMagicNo)>=MaxOrders)
        {
          dBuyPrice=dFLowestPrice(OP_BUY,OP_BUYLIMIT,OP_BUYSTOP,EAMagicNo,9999999);
          dSL=dBuyPrice-(MathMax(dSL,dStopLv*Point));
          dSL=NormalizeDouble(dSL,Digits);
          
          dBuyOP=dFHighestPrice(OP_BUY,OP_BUYLIMIT,OP_BUYSTOP,EAMagicNo,0);
          
          for (i=1; i<=iTotalOrders; i++)
          {
            if (OrderSelect(i-1,SELECT_BY_POS,MODE_TRADES)==true)
            {
              if (OrderSymbol()==Symbol() && OrderMagicNumber()==EAMagicNo && OrderType()==OP_BUY && OrderOpenPrice()==dBuyOP)
              {
                if (OrderStopLoss()!=dSL)
                {
                  iTicket=OrderModify(OrderTicket(),OrderOpenPrice(),dSL,OrderTakeProfit(),0,clrDodgerBlue);
                  
                  if (iTicket<0)
                    Print ("Modify Buy SL Error Code: ", GetLastError());
                    
                  break;
                }
              }
            }
          }
        }
      }
      else
      {
        if (iFCheckOrdersPart(OP_SELL,EAMagicNo)>=MaxOrders)
        {
          dSellPrice=dFHighestPrice(OP_SELL,OP_SELLLIMIT,OP_SELLSTOP,EAMagicNo,0);
          dSL=dSellPrice+(MathMax(dSL,dStopLv*Point));
          dSL=NormalizeDouble(dSL,Digits);
          
          dSellOP=dFLowestPrice(OP_SELL,OP_SELLLIMIT,OP_SELLSTOP,EAMagicNo,99999999);
          
          for (i=1; i<=iTotalOrders; i++)
          {
            if (OrderSelect(i-1,SELECT_BY_POS,MODE_TRADES)==true)
            {
              if (OrderSymbol()==Symbol() && OrderMagicNumber()==EAMagicNo && OrderType()==OP_SELL && OrderOpenPrice()==dSellOP)
              {
                if (OrderStopLoss()!=dSL)
                {
                  iTicket=OrderModify(OrderTicket(),OrderOpenPrice(),dSL,OrderTakeProfit(),0,clrDeepPink);
                  
                  if (iTicket<0)
                    Print ("Modify Sell SL Error Code: ", GetLastError());
                }
              }
            }
          }
        }
      }
    }
  }

void vFCommentInit()
  {
    sGComments="";
  }
  
void vFCommentAdd(string sComment)
  {
    sComment=sComment+"\n";
    sGComments=sGComments+sComment;
  }
  
void vFCommentShow()
  {
    Comment(sGComments);
  }
  
double dFAvgRange(ENUM_TIMEFRAMES eTimeframe)
  {
    return(iATR(NULL,eTimeframe,64,1));
  }

void vFOrderInfo(int& iOrderBuy, double& dLotBuy, double& dProfitBuy, double& dPointBuy,
                 int& iOrderSell, double& dLotSell, double& dProfitSell, double& dPointSell)
  {
    int i, iTotalOrders=OrdersTotal();
    
    iOrderBuy=0; iOrderSell=0;
    dLotBuy=0.00; dLotSell=0.00;
    dProfitBuy=0.00; dProfitSell=0.00;
    dPointBuy=0.00; dPointSell=0.00;
    
    if (iTotalOrders>0)
    {
      for (i=1; i<=iTotalOrders; i++)
      {
        if (OrderSelect(i-1,SELECT_BY_POS,MODE_TRADES)==true)
        {
          if (OrderSymbol()==Symbol() && OrderMagicNumber()==EAMagicNo)
          {
            if (OrderType()==OP_BUY)
            {
              iOrderBuy+=1;    // iOrderBuy=iOrderBuy+1
              dLotBuy+=OrderLots();
              dProfitBuy+=OrderProfit()+OrderSwap()+OrderCommission();
              if (ObjectFind(0,"BuyAverage")==0)
                dPointBuy=(Bid-dFReturnPrice("BuyAverage"))/Point;
              else
                dPointBuy+=(Bid-OrderOpenPrice())/Point;
            }
            else if (OrderType()==OP_SELL)
            {
              iOrderSell+=1;
              dLotSell+=OrderLots();
              dProfitSell+=OrderProfit()+OrderSwap()+OrderCommission();
              if (ObjectFind(0,"SellAverage")==0)
                dPointSell=(dFReturnPrice("SellAverage")-Ask)/Point;
              else
                dPointSell+=(OrderOpenPrice()-Ask)/Point;
            }
          }
        }
      }
    }
  
  }

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
//---

  }
//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
//---
    double dTickValue, dAvgRange;
    string sEAComment, sAllowBuy, sAllowSell, sAllowOpposite;
    int iOrderBuy=0, iOrderSell=0;
    double dLotBuy=0, dProfitBuy=0, dPointBuy=0,
           dLotSell=0, dProfitSell=0, dPointSell=0,
           dTotalProfit=0;
    
    vFCommentInit();
    
    vFCommentAdd(">> "+ WindowExpertName()+" v1.00");
    
    if (EAComment=="")  sEAComment="-N/A-";
    else                sEAComment=EAComment;
    
    vFCommentAdd(">> EA Magic No: "+(string)EAMagicNo+" ; EA Comment: "+sEAComment);
    vFCommentAdd("");

    vFOpenOrder();
    vFHandleAvg();
    
    if (iFCheckOrdersPart(OP_BUY,EAMagicNo)>1)
      vFCountBEP(OP_BUY);
    else
      ObjectDelete(0,"BuyAverage");
      
    if (iFCheckOrdersPart(OP_SELL,EAMagicNo)>1)
      vFCountBEP(OP_SELL);
    else
      ObjectDelete(0,"SellAverage");
      
    if (iFCheckOrdersPart(OP_BUY,EAMagicNo)>0)
      vFHandleSLTP(OP_BUY);
    
    if (iFCheckOrdersPart(OP_SELL,EAMagicNo)>0)
      vFHandleSLTP(OP_SELL);
      
    dTickValue=MarketInfo(NULL,MODE_TICKVALUE);
    
    dAvgRange=(dFAvgRange(PERIOD_MN1)+dFAvgRange(PERIOD_W1))/2/Point;
    
    if (AllowBuy)  sAllowBuy="BUY ";
    if (AllowSell) sAllowSell="SELL ";
    if (AllowOppositeOrder) sAllowOpposite="(Opposite=true)";
    
    vFOrderInfo(iOrderBuy,dLotBuy,dProfitBuy,dPointBuy,iOrderSell,dLotSell,dProfitSell,dPointSell);
    dTotalProfit=dProfitBuy+dProfitSell;
    
    vFCommentAdd(">> Operation: "+sAllowBuy+sAllowSell+sAllowOpposite);
    vFCommentAdd(">> Lot Size: " + DoubleToStr(dGLotSize,2)+" (Tick Value: " +DoubleToStr(dTickValue,2)+" "+AccountCurrency()+")");
    vFCommentAdd(">> Avg Range: " + DoubleToStr(dAvgRange,2)+" pips");
    vFCommentAdd(">> Min Distance: " + DoubleToStr(MinOrderDistance,2)+" pips ; Max Orders: " +(string)MaxOrders);
    vFCommentAdd(">> TP: " + DoubleToStr(TP,2)+" pips ; SL: " + DoubleToStr(SL,2)+" pips");
    vFCommentAdd("");
    vFCommentAdd(">> BUY :: Order: " + (string)iOrderBuy+" ; Total Lots: " + DoubleToStr(dLotBuy,2)+" lots ; Profit: " + DoubleToStr(dProfitBuy,2)+" "+AccountCurrency()+" ("+DoubleToStr(dPointBuy,2)+" point)");
    vFCommentAdd(">> SELL :: Order: " + (string)iOrderSell+" ; Total Lots: " + DoubleToStr(dLotSell,2)+" lots ; Profit: " +DoubleToStr(dProfitSell,2)+" "+AccountCurrency()+" ("+DoubleToStr(dPointSell,2)+" point)");
    vFCommentAdd(">> TOTAL: " +DoubleToStr(dTotalProfit,2)+" "+AccountCurrency());

    vFCommentShow();
  }
//+------------------------------------------------------------------+

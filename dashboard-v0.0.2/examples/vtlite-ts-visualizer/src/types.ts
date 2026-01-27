// src/types.ts
export interface TimeSeriesDatum {
    config: string;
    sim: number;
    time: number;
    ChS: number;
    DisS: number;
    SCS: number;
    WPQ: number;
    WSQ: number;
    kBS: number;
    kWS: number;
    lam_DAQ: number;
    lam_RT: number;
    pRBDS: number;
    pRBUS: number;
    pRWDS: number;
    pRWUS: number;
    pWDSQ: number;
    pWRS: number;
    pWSQ: number;
    v1: number;
    v2: number;
    WS: number;
    pWDS: number;
    pWS: number;
    "Case Study": string;
    Location: string;
  }
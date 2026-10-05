/* ORION product UI configuration. This surface is separate from the manual engineering Remote. */
window.STRATA_CONFIG={
 product:{name:'ORION',surface:'product-ui',remoteFrozen:true},
 /* No engineering-Remote links are rendered here. Manual engineering execution is handled separately by TheHands. */
 legacy:[],
 poll:{idleMs:2000,activeMs:800,hiddenMs:8000,statusTimeoutMs:8000,commandTimeoutMs:30000},
 link:{staleAfterMs:6000,reconnectingAfterMs:20000,offlineAfterMs:90000},
 freshWindowMs:900000
};

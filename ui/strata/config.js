/* ORION product UI configuration. This surface is separate from the frozen V1 Remote. */
window.STRATA_CONFIG={
 product:{name:'ORION',surface:'product-ui',remoteFrozen:true},
 /* No legacy/Remote links are rendered in the product UI. V1 is used separately as the engineering control path. */
 legacy:[],
 poll:{idleMs:2000,activeMs:800,hiddenMs:8000,statusTimeoutMs:8000,commandTimeoutMs:30000},
 link:{staleAfterMs:6000,reconnectingAfterMs:20000,offlineAfterMs:90000},
 freshWindowMs:900000
};

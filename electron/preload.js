const { contextBridge } = require("electron");

contextBridge.exposeInMainWorld("LagSense", {
  version: "1.0.0"
});

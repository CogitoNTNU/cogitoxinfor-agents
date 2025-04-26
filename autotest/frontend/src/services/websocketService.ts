// websocketService.ts
// Talks to the Browser‑Box bridge (Socket.IO on :3100)

import { io, Socket } from "socket.io-client";

type JSONValue = string | number | boolean | null | { [x: string]: JSONValue } | JSONValue[];

class WebSocketService {
  private socket: Socket | null = null;

  /* ------------------------------------------------------------------ */
  /* Connection                                                         */
  /* ------------------------------------------------------------------ */
  connect(): Promise<boolean> {
    return new Promise((resolve) => {
      if (this.socket?.connected) return resolve(true);

      this.socket = io("http://localhost:3100", { transports: ["websocket"] });

      this.socket.on("connect", () => {
        console.log("[ws] connected");
        resolve(true);
      });

      this.socket.on("connect_error", (err) => {
        console.error("[ws] connect_error:", err);
        resolve(false);
      });
    });
  }

  disconnect() {
    this.socket?.disconnect();
    this.socket = null;
  }

  /* ------------------------------------------------------------------ */
  /* Bridge actions                                                     */
  /* ------------------------------------------------------------------ */
  startBox(opts: Record<string, JSONValue> = {}) {
    this.socket?.emit("start-box", opts);
  }

  stopBox() {
    this.socket?.emit("stop-box");
  }

  execute(tool: string, input: Record<string, JSONValue> = {}, cb?: (res: any) => void) {
    if (!this.socket) return console.error("[ws] not connected");
    this.socket.emit("execute", { tool, input }, cb);
  }

  /* ------------------------------------------------------------------ */
  /* Event subscriptions                                                */
  /* ------------------------------------------------------------------ */
  onStatus(cb: (s: any) => void) {
    this.socket?.on("box-status", cb);
    return () => this.socket?.off("box-status", cb);
  }

  onScreenshot(cb: (data: { data: string }) => void) {
    this.socket?.on("screenshot", cb);
    return () => this.socket?.off("screenshot", cb);
  }

  onLog(cb: (line: string, stream: "stdout" | "stderr") => void) {
    this.socket?.on("box-log", (payload) => cb(payload.data, payload.type));
    return () => this.socket?.off("box-log", cb);
  }
}

export const websocketService = new WebSocketService();

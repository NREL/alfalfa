import { v1 as uuidv1 } from "uuid";
import { getHashValue, setHashValue } from "./utils";

const intervalMs = 250;

class Advancer {
  // This class pertains to advancing a simulation.
  //
  // The task is to notify the simulation alfalfa_worker of a (http) request to advance the simulation,
  // After notifying the simulation alfalfa_worker of a request to advance, the webserver must
  // wait for the simulation step to complete, and only then return a response to the http client.
  //
  // A redis database is used as the primary mechanism to
  // communicate between the webserver and the simulation alfalfa_worker
  //
  // For each request to advance a simulation, communication involves
  // 1. A redis key of the form ${siteRef}:control which can have the value idle | advance | running
  //    A request to advance can only be fulfilled if the simulation is currently in idle state
  // 2. A redis notification from the webserver on the channel "siteRef" with message "advance"
  // 3. A redis notification from the alfalfa_worker on the channel "siteRef" with message "complete",
  //    signaling that the simulation is done advancing to the simulation
  constructor(redis, pub, sub) {
    this.redis = redis;
    this.pub = pub;
    this.sub = sub;
    this.handlers = {};

    this.sub.on("message", (channel, message) => {
      if (message === "complete") {
        if (this.handlers.hasOwnProperty(channel)) {
          this.handlers[channel](message);
        }
      }
    });
  }

  advance(siteRefs) {
    return new Promise((resolve) => {
      let response = {};
      let pending = siteRefs.length;

      const advanceSite = (siteRef) => {
        const channel = siteRef;

        // Cleanup the resources for advance and finalize the promise
        let interval;
        const finalize = (success, message = "") => {
          clearInterval(interval);
          this.sub.unsubscribe(channel);
          response[siteRef] = { status: success, message: message };
          --pending;
          if (pending === 0) {
            resolve(response);
          }
        };

        const notify = () => {
          this.handlers[channel] = () => {
            finalize(true, "success");
          };

          this.sub.subscribe(channel);
          const uuid = uuidv1();
          this.pub.publish(channel, JSON.stringify({ message_id: uuid, method: "advance" }));

          // This is a failsafe if for some reason we miss a notification
          // that the step is complete
          // Check if the simulation has gone back to idle
          let intervalCounts = 0;
          interval = setInterval(async () => {
            const control = await getHashValue(this.redis, siteRef, "control");
            const value = await getHashValue(this.redis, siteRef, uuid);
            if (!value) return;
            finalize(JSON.parse(value).status === "ok", value);
            if (control === "idle") {
              // If the control state is idle, then assume the step has been made
              // and resolve the advance promise, this might happen if we miss the notification for some reason
              finalize(true, "success");
            } else {
              ++intervalCounts;
            }
            if (intervalCounts > 60000 / intervalMs) {
              console.error(`Simulation with id ${siteRef} timed out while trying to advance`);
              finalize(false, "no simulation reply");
            }
          }, intervalMs);
        };

        // Put siteRef:control key into "advance" state
        this.redis.watch(siteRef, async (err) => {
          if (err) throw err;

          const control = await getHashValue(this.redis, siteRef, "control");
          // if control not equal to idle then abort the request to advance and return to client
          if (control === "idle") {
            // else proceed to advance state, this node has exclusive control over the simulation now
            await setHashValue(this.redis, siteRef, "control", "advance");
            notify();
          } else {
            finalize(true, "busy");
          }
        });
      };

      for (const site of siteRefs) {
        advanceSite(site);
      }
    });
  }
}

export { Advancer };

<template>
  <div id="container">
    <!-- Stream camera feed -->
    <div id="stream">
      <video id="video" autoplay="true" />
      <canvas id="canvas" style="display: none;" />
    </div>

    <div id="hud">
      <!-- Stream counter -->
      <stream-count
        :ws-stream-state="wsStreamState"
      />

      <!-- Stream timer -->
      <stream-time
        :ws-stream-state="wsStreamState"
      />

      <!-- Stream controls -->
      <stream-controls
        :ws-stream-state="wsStreamState"
        :camera-icon-active="cameraIconActive"
      />

      <!-- Stream error handling -->
      <transition name="fade">
        <stream-error-banner
          :stream-error="streamError"
        />
      </transition>

      <!-- Stream sidebar -->
      <stream-sidebar />

      <!-- TEMP GPS -->
      <stream-speed
        v-if="streamSpeed"
      />
      <!--  -->
    </div>
  </div>
</template>

<script>
import StreamCount from "./StreamCount";
import StreamControls from "./StreamControls";
import StreamTime from "./StreamTime";
import StreamErrorBanner from "./StreamError";
import StreamSidebar from "./StreamSidebar";
import StreamSpeed from "./StreamSpeed";
import * as NoSleep from "nosleep.js";
import { v4 as uuidv4 } from "uuid";
import { eventBus } from "@/main";
import { checkLoggedIn } from "../../utils/loggedInCheck";

export default {
  name: "StreamingClient",

  components: {
    StreamCount,
    StreamTime,
    StreamControls,
    StreamErrorBanner,
    StreamSidebar,
    StreamSpeed,
  },

  data () {
    return {
      // -- 
      // Env properties
      developMode: process.env.VUE_APP_APP_MODE || null, // development or production mode

      apiWebSocketUrl: process.env.VUE_APP_API_WS_URL, // WebSocket connection URL
      minimumAnalyzeFrameHeight: process.env.VUE_APP_MINIMUM_ANALYZE_FRAME_HEIGHT, // minimum pixels frame should have when going through analyzer
      prefCameraOption: process.env.VUE_APP_DEFAULT_CAMERA_DIRECTION, // "environment" or "user"
      captureFrameIntervalTime: process.env.VUE_APP_CAPTURE_INTERVAL, // time between sending frames

      // -- 
      // UI properties
      // switchIconActive: false, // manual/auto switch
      cameraIconActive: true, // flip camera button, true = visible
      streamSpeed: false, // show / hide speed controls, true = show

      // --
      // Network properties
      hasNetworkConnection: navigator.onLine, // network state, true = online

      // -- 
      // Stream properties
      camQuality: {
        min: {
          width: 1280,
          height: 720,
        }, // minimum quality of frame, lower quality cameras can't stream
        ideal: {
          width: 1280,
          height: 720,
        }, // ideal quality of frame
      },
      video: null, // camera feed, HTML element
      videoLivestream: null, // camera feed, livestream
      canvas: null, // camera feed overlay to capture frame
      intervalCaptureFrame: null, // interval func
      intervalReconnectStream: null, // interval reconnect to WebSocket funcs

      // --
      // Stream error properties
      streamError: {
        state: false, // true = error occured
        message: null, // error message to display
        level: 1, // 1 = error, 2 = warning
      },

      // -- 
      // WebSocket properties
      wsConnection: null, // WebSocket live connection
      wsStreamState: {
        connecting: false,
        open: false,
        closed: true,
        paused: false,
      }, // WebSocket Stream States

      // -- 
      // GPS based properties
      location: {
        lat: null,
        lng: null,
        speed: null, // km/h (m/s * 3.6)
        minDrivingSpeed: process.env.VUE_APP_MINIMUM_DRIVING_SPEED, // minimum speed user should be driving to send frames
        maxDrivingSpeed: process.env.VUE_APP_MAXIMUM_DRIVING_SPEED, // maximum speed user should be driving to send frames
        currentSpeedGood: false, // determine if current speed is okay (within min/max speed limits)
      },
    };
  },

  watch: {
    wsStreamState (obj) {
      // Check when paused / unpaused
      // If paused, try to reconnect
      if (obj.paused) {
        this.intervalReconnectStream = setInterval(
          this.startStream,
          5000,
        );
        return;
      }

      // If unpaused, stop interval
      clearInterval(this.intervalReconnectStream);
      return;
    },
  },

  mounted () {
    // Check if the user is already logged in,
    // if so, create uuid streamId
    this.checkUserType();

    // Initial setup
    this.setup();

    // EventBus for receiving control usage
    eventBus.$on("startStreaming", () => {
      this.startStream();
    });
    eventBus.$on("stopStreaming", () => {
      this.stopStream();
    });
    eventBus.$on("flipCameraEmitted", () => {
      this.flipCamera();
    });

    // EventBus for receiving min / max speed changes
    eventBus.$on("minSpeedChanged", (val) => {
      this.location.minDrivingSpeed = val;
    });
    eventBus.$on("maxSpeedChanged", (val) => {
      this.location.maxDrivingSpeed = val;
    });

    // Eventbus for receiving sidebar dev tools switches
    eventBus.$on("toggleSpeed", () => {
      this.streamSpeed = !this.streamSpeed;
      // Set localStogage speed to keep speed that has been set
      if (!this.streamSpeed) {
        localStorage.minSpeed = this.location.minDrivingSpeed;
        localStorage.maxSpeed = this.location.maxDrivingSpeed;
      }
    });
  },

  methods: {
    setup () {
      // Initialize and activate noSleep to prevent sleep modus
      const noSleep = new NoSleep();
      noSleep.enable();

      // Set vars
      this.video = document.getElementById("video");
      this.canvas = document.getElementById("canvas");

      // Show camera feed
      this.startCameraFeed();

      // Get and watch GPS position
      this.startLocation();

      // Check and track network state
      this.checkNetworkState();
    },

    // ----
    // UI funcs
    // ----

    flipCamera () {
      // Toggle between "user" and "environment"
      if (this.prefCameraOption === "user") {
        this.prefCameraOption = "environment";
      } else {
        this.prefCameraOption = "user";
      }

      // Stop current camera feed
      this.stopCameraFeed(this.videoLivestream);

      // Start new feed with different camera
      this.startCameraFeed();
    },

    // ----

    errorHandling (message, level, timeout, time = 0) {
      // Set error message and bool to true
      this.streamError = {
        state: true,
        message: message,
        level: level,
      };

      // Add removal process of error message if needed
      if (timeout) {
        setTimeout(() => {
          this.streamError = {
            state: false,
            message: null,
            level: 1,
          };
        }, time);
      }
    },

    // ----
    // Network state funcs
    // ----

    checkNetworkState () {
      // Add network eventlistener
      this.addNetworkEventListener();

      // Check current (initial) network connection
      this.handleNetworkStateChange();
    },

    // ----

    addNetworkEventListener () {
      // Event listners for going online / offline
      window.addEventListener("online", this.handleNetworkStateChange);
      window.addEventListener("offline", this.handleNetworkStateChange);
    },

    // ----

    handleNetworkStateChange () {
      // Retreive current network state
      this.hasNetworkConnection = navigator.onLine;

      // If network connection
      if (this.hasNetworkConnection) {
        // Delete error
        this.streamError = {
          state: false,
          message: null,
          level: 1,
        };
        return;
      }

      // Set network error
      const message = "No Internet connection";
      this.errorHandling(message, 1, false);

      // If state went from online to offline while streaming
      if (this.wsStreamState.open && !this.hasNetworkConnection) {
        // Pause stream
        this.pauseStream();
        return;
      }
    },

    // ----
    // Start and Stop camera feed
    // ----

    startCameraFeed () {
      // Get camera feed
      const video = this.video;

      // Create camera feed options
      const currentConstraints = {
        video: {
          facingMode: this.prefCameraOption,
          width: { min: this.camQuality.min.width, ideal: this.camQuality.ideal.width },
          height: { min: this.camQuality.min.height, ideal: this.camQuality.ideal.height },
        },
        audio: false,
      };

      const curScope = this;

      // Set camera feed options
      navigator.mediaDevices
        .getUserMedia(currentConstraints)
        .then(function (stream) {
          curScope.videoLivestream = stream;
          video.srcObject = stream;
          video.play();
        })
        .catch(function (err) {
          console.log("Something went wrong with setup of camera feed");
          console.error(err);
        });

      video.addEventListener("canplay", this.setVideoCanvasDimensions, false);
    },

    // ----

    stopCameraFeed (stream) {
      // Stop every track (a/v)
      stream.getTracks().forEach(track => {
        track.stop();
      });
    },

    // ----
    // Set video and canvas dimensions
    // ----

    setVideoCanvasDimensions () {
      // Get dimensions of current camera feed
      const streamFeedWidth = this.video.videoWidth;
      const streamFeedHeight = this.video.videoHeight;

      // Set dimensions to both video and canvas
      this.video.setAttribute("width", streamFeedWidth);
      this.video.setAttribute("height", streamFeedHeight);
      this.canvas.setAttribute("width", streamFeedWidth);
      this.canvas.setAttribute("height", streamFeedHeight);
    },

    // ----
    // GPS based funcs
    // ----

    startLocation () {
      // Set options
      const geoOptions = {
        enableHighAccuracy: true,
      };

      // Fetch location once
      navigator.geolocation.getCurrentPosition(this.updatePosition, this.positionError, geoOptions);

      // Keep watching location
      navigator.geolocation.watchPosition(this.updatePosition, this.positionError, geoOptions);
    },

    // ----

    updatePosition (position) {
      // Set new GPS location values
      this.location.lat = position.coords.latitude;
      this.location.lng = position.coords.longitude;
      this.location.speed = position.coords.speed * 3.6 || 0; // m/s to km/h = x * 3.6

      // Send new speed to StreamSpeed.vue
      eventBus.$emit("speedUpdated", (this.location.speed).toFixed(1));
    },

    // ----

    positionError (err) {
      console.warn(`ERROR(${err.code}): ${err.message}`);
    },

    // ----

    checkDrivingSpeed () {
      // Check if vehicle is moving (above minimum driving speed & below maximum driving speed)
      if (this.location.speed >= this.location.minDrivingSpeed && this.location.speed <= this.location.maxDrivingSpeed) {
        // Current speed is okay
        this.location.currentSpeedGood = true;

        // Remove speed warning
        this.streamError = {
          state: false,
          message: null,
          level: 1,
        };

        return true;
      }

      // Current speed is beyond limits
      this.location.currentSpeedGood = false;

      // If driving too slow
      if (this.location.speed < this.location.minDrivingSpeed) {
        console.debug(`Speed must me above ${this.location.minDrivingSpeed} km/h, but isn't`);

        // Set speed warning
        if (!this.streamError.state) {
          const message = "You are driving too slow to send images";
          this.errorHandling(message, 2, false);
        }

        return false;
      }

      // If driving too fast
      console.debug(`Speed must me below ${this.location.maxDrivingSpeed} km/h, but isn't`);
      
      // Set speed warning
      if (!this.streamError.state) {
        const message = "You are driving too fast to send images";
        this.errorHandling(message, 2, false);
      }

      return false;
    },

    // ----
    // Start, Stop and Pause stream funcs
    // ----

    startStream () {
      // Setup connection with WebSocket server and start stream
      if (!this.hasNetworkConnection) {
        console.debug("Not trying to setup WebSocket without network connection");
        return;
      }

      this.setupWebSocket();
    },

    // ----

    stopStream () {
      // Close webSocket connection
      this.wsConnection.close();

      // Set WebSocket state
      this.wsStreamState = {
        connecting: false,
        open: false,
        closed: true,
        paused: false,
      };

      // Show camera flip icon
      this.cameraIconActive = true;

      // Reset timer
      eventBus.$emit("resetStreamTimer");
    },

    // ----

    pauseStream () {
      // Delete WebSocket connection
      this.wsConnection = null;

      // Set Websocket state 'paused' to true
      this.wsStreamState = {
        connecting: false,
        open: false,
        closed: false,
        paused: true,
      };
      
      // Pause timer
      eventBus.$emit("pauseStreamTimer");
    },

    // ----
    // Capture frame funcs
    // ----

    startCaptureFrameInterval () {
      clearInterval(this.intervalCaptureFrame);
      // Interval function to capture frame from video feed
      this.intervalCaptureFrame = setInterval(
        this.captureFrame,
        this.captureFrameIntervalTime
      );
    },

    // ----

    stopCaptureFrameInterval () {
      // Stop nterval function to capture frame from video feed
      clearInterval(this.intervalCaptureFrame);
    },

    // ----

    captureFrame () {
      // Check if car is moving faster than minimum speed
      const isDriving = this.checkDrivingSpeed() || false;

      if (!isDriving) {
        console.debug(`Not capturing frame. Car is moving too slow (${this.location.speed.toFixed(1)} km/h)`);
        return;
      }

      // Get canvas to 'draw' frame on
      const context = this.canvas.getContext("2d");

      // Draw frame on canvas
      context.drawImage(this.video, 0, 0, this.video.videoWidth, this.video.videoHeight);

      // Convert 'drawing' to dataURL (base64)
      const frame = this.canvas.toDataURL("image/jpeg");

      // Send frame as WebSocket message
      this.sendWebSocketMsg(frame);
    },

    // ----
    // WebSocket funcs
    // ----

    setupWebSocket () {
      console.debug("Trying to establish WebSocket connection");

      // Set WebSocket state
      this.wsStreamState = {
        connecting: true,
        open: false,
        closed: false,
        paused: false,
      };

      // Setup connection with WebSocket server URL:PORT/ENDPOINT
      const webSocketUrl = this.apiWebSocketUrl + "/stream";
      this.wsConnection = new WebSocket(webSocketUrl);

      // WebSocket events
      this.wsConnection.onopen = this.receiveWebSocketMsgOnOpen;
      this.wsConnection.onclose = this.receiveWebSocketMsgOnClose;
      this.wsConnection.onmessage = this.receiveWebSocketMsg;
      this.wsConnection.onerror = this.receiveWebSocketMsgOnError;
    },

    // ----

    receiveWebSocketMsgOnOpen () {
      console.debug("WebSocket connection established");
      
      // Set WebSocket state
      this.wsStreamState = {
        connecting: false,
        open: true,
        closed: false,
        paused: false,
      };

      // Hide camera flip icon
      this.cameraIconActive = false;

      // Start timer
      eventBus.$emit("startStreamTimer");

      // Start capture frames
      this.startCaptureFrameInterval();
    },

    // ----

    receiveWebSocketMsgOnClose () {
      console.debug("WebSocket connection closed");

      // Remove speed warning if speed warning
      if (!this.location.currentSpeedGood) {
        this.streamError = {
          state: false,
          message: null,
          level: 1,
        };
      }

      // Stop capturing and sending frames
      this.stopStream();
      this.stopCaptureFrameInterval();

      // Delete webSocket connection
      this.wsConnection = null;
    },

    // ----

    receiveWebSocketMsg (msg) {
      console.debug("WebSocket message received");
      const ws_message = JSON.parse(msg.data);

      if (ws_message.type == "error") {
        console.error(ws_message.error, ws_message.content);

        const message = "Data error occurred, please try again";
        this.errorHandling(message, 1, true, 3000);
      }
      else {
        console.log(ws_message);
      }
    },

    // ----

    receiveWebSocketMsgOnError () {
      console.debug("WebSocket connection failed to establish");

      // Set WebSocket state
      this.wsStreamState = {
        connecting: false,
        open: false,
        closed: true,
        paused: false,
      };

      // Set error
      const message = "Connection to server failed";
      this.errorHandling(message, 1, true, 5000);
    },

    // ----

    sendWebSocketMsg (frame) {
      console.debug("WebSocket send message");

      // Set message to send
      const message = {
        img: frame,
        stream_id: localStorage.streamId,
        lat: this.location.lat,
        lng: this.location.lng,
        timestamp: this.$moment().format("YYYY-MM-DD HH:mm:ss.SSS"),
        stream_meta: {
          user_type: localStorage.userType,
          user_id: localStorage.userId || "demo",
          speed_kph: this.location.speed,
          set_min_speed_kph: this.location.minDrivingSpeed,
          set_max_speed_kph: this.location.maxDrivingSpeed,
        },
      };

      // Send message to webSocket API
      this.wsConnection.send(JSON.stringify(message));
    },

    // ----
    // Validation funcs
    // ----

    checkUserType () {
      const loggedIn = checkLoggedIn();
      if (!loggedIn) {
        this.$router.push("/welcome");
        return;
      }

      // Get uuid
      const uuid = uuidv4();

      // Set localStorage
      localStorage.streamId = uuid;

      // Send new streamId to other components
      eventBus.$emit("newStreamId", uuid);
    },
  },
};
</script>

<style lang="scss" scoped>
#container {
  display: flex;
  position: relative;
  align-items: center;
  margin: 0 auto;
  width: 100vw;
  height: 100vh;
  overflow: hidden;

  @media (orientation: landscape) {
    max-width: 896px;
    max-height: 414px;
  }
}

#stream {
  position: relative;
  width: 100%;

  #video {
    width: 100%;
    height: auto;
  }
}

#hud {
  position: absolute;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
}

video {
  max-width: none !important;
}

.fade-enter-active {
  animation: slide-in-top 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94) both;
}

.fade-enter,
.fade-leave-to {
  animation: slide-in-top 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94) reverse;
}

@keyframes slide-in-top {
  0% {
    -webkit-transform: translateY(-1000px);
    transform: translateY(-1000px);
    opacity: 0;
  }

  100% {
    -webkit-transform: translateY(0);
    transform: translateY(0);
    opacity: 1;
  }
}
</style>

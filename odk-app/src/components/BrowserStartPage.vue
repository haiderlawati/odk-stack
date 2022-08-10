<template>
  <odk-container
    :fullwidth="true"
    :fullheight="true"
  >
    <div class="image-section" aria-hidden="true">
      <img src="@/assets/pwa/intro.png" alt="Object Detection Kit abstract figure">
    </div>

    <div class="text-section">
      <h1>Object Detection Kit</h1>
      <p>Keep streets clean by scanning while driving</p>

      <b-button
        v-if="pwaCapable"
        ref="addButton"
        type="is-primary"
        rounded
        outlined
        @click.native="clickAddAppButton"
      >
        Install App
      </b-button>

      <!-- SUPPORTED BROWSERS MANUAL -->
      <div v-if="activeVendor === 'chrome' || activeVendor === 'edgeAndroid' || activeVendor === 'firefoxAndroid'">
        <p>
          To continue you must use the <strong>install app</strong>
        </p>

        <p>
          <router-link :to="{ name:'installation-manual', params: { openCard: activeVendor } }">
            How do I install a PWA?
          </router-link>
        </p>
      </div>

      <!-- UNSUPPORTED BROWSERS MANUAL -->
      <div v-else-if="activeVendor === 'iOS'">
        <p>iOS is not supported</p>

        <p>
          <router-link :to="{ name:'installation-manual', params: { openCard: activeVendor } }">
            Why?
          </router-link>
        </p>
      </div>

      <div v-else-if="activeVendor === 'othersAndroid'">
        <p>Use a different browser</p>

        <p>
          <router-link :to="{ name:'installation-manual', params: { openCard: activeVendor } }">
            Which browser?
          </router-link>
        </p>
      </div>

      <div v-else>
        <p>This app is made for Android phones</p>

        <p>
          <router-link :to="{ name:'installation-manual', params: { openCard: activeVendor } }">
            Why?
          </router-link>
        </p>
      </div>
    </div>
  </odk-container>
</template>

<script>
import { startupCheck } from "@/mixins/startupCheck";
import { isChrome, isFirefox, isMSEdge, isAndroid, isiOS } from "@/utils/detect";

export default {
  name: "BrowserStartPage",

  mixins: [ startupCheck ],

  data () {
    return {
      activeVendor: null,
      pwaCapable: false,
      deferredPrompt: null,
    };
  },

  beforeMount () {
    // Check if the user is already logged in,
    // if so, go to streaming client
    this.checkUserType();
  },

  mounted () {
    // Without the PWA installed the user cannot access the video stream.
    this.checkAppMode();
    this.checkBrowserType();

    // PWA installation prompt event.
    window.addEventListener("beforeinstallprompt", e => {
      e.preventDefault();
      this.deferredPrompt = e;
      this.pwaCapable = true;
    });
  },

  methods: {
    clickAddAppButton () {
      // Show the deferred prompt.
      this.deferredPrompt.prompt();

      // Wait for the user to respond to the prompt.
      this.deferredPrompt.userChoice.then(choiceResult => {
        if (choiceResult.outcome === "accepted") {
          console.log("User accepted the A2HS prompt");
        } else {
          console.log("User dismissed the A2HS prompt");
        }

        this.deferredPrompt = null;
      });
    },

    checkUserType () {
      // if localStorage.UserType exists (change streamId for new session)
      if (localStorage.userType) {
        this.$router.push("/client");
      }
    },

    checkBrowserType () {
      if (isAndroid() && isChrome()) {
        console.log("Browser: Chromium, Device: Android");
        this.activeVendor = "chrome";
      } else if (isAndroid() && isMSEdge()) {
        console.log("Browser: Microsoft Edge, Device: Android");
        this.activeVendor = "edgeAndroid";
      } else if (isAndroid() && isFirefox()) {
        console.log("Browser: Mozilla Firefox, Device: Android");
        this.activeVendor = "firefoxAndroid";
      } else if (isAndroid()) {
        console.log("Device and browser: unsupported");
        this.activeVendor = "othersAndroid";
      } else if (isiOS()) {
        console.log("Browser: WebKit-based, Device: iOS");
        this.activeVendor = "iOS";
      } else {
        console.log("Browser: n/a, Device: Not Android or iOS");
        this.activeVendor = "desktop";
      }
    },
  },
};
</script>

<style lang="scss" scoped>
.image-section {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 50%;

  img {
    transition: transform 150ms ease;
    width: 100%;
    object-fit: contain;
  }
}

.text-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0 2rem;
  height: 50%;
  min-height: 20rem;

  .button {
    margin: 1.5rem auto;
  }
}

@media (orientation: landscape) {
  .image-section {
    width: 45%;
    height: auto;

    img {
      height: 100%;
      transform: translateX(-15%);
    }
  }

  .text-section {
    width: 55%;
    height: auto;
  }
}
</style>

<template>
  <odk-container>
    <div
      class="image-section"
      aria-hidden="true"
    >
      <onboarding-animation />
    </div>

    <div class="text-section">
      <div class="text-section-header">
        <h1 class="odk-title">Voordat u begint</h1>
      </div>

      <div class="text-section-buttons">
        <b-button
          expanded
          outlined
          rounded
          type="is-primary"
          :class="{ 'check-item-complete' : landscapeOrientation}"
        >
          <div>
            <img v-if="landscapeOrientation" class="checkmark" src="@/assets/ui/checkmark.svg">
            <span :class="{ 'buttonspan-margin' : !landscapeOrientation }">Houd uw telefoon liggend</span>
          </div>
        </b-button>

        <b-button
          class="loc-check-button"
          expanded
          outlined
          rounded
          type="is-primary"
          :class="{ 'check-item-complete' : locationPermission}"
          @click="askLocPermission()"
        >
          <div>
            <img v-if="locationPermission" class="checkmark" src="@/assets/ui/checkmark.svg">
            <span :class="{ 'buttonspan-margin' : !locationPermission }" class="buttonspan">GPS-locatie inschakelen</span>
          </div>
        </b-button>

        <b-button
          expanded
          outlined
          rounded
          type="is-primary"
          :disabled="!locationPermission"
          :class="{ 'check-item-complete' : camPermission}"
          class="camera-button camera-check-button"
          @click="askCamPermission()"
        >
          <div>
            <img v-if="camPermission" class="checkmark" src="@/assets/ui/checkmark.svg">
            <span :class="{ 'buttonspan-margin' : !camPermission }" class="buttonspan2">Camera inschakelen</span>
          </div>
        </b-button>
      </div>
      <p class="tip">Als u deze stappen niet volgt, zal u ODK niet kunnen gebruiken</p>
    </div>
  </odk-container>
</template>

<script>
import OnboardingAnimation from "./OnboardingAnimation.vue";

export default {
  name: "ChecklistPage",

  components: {
    "onboarding-animation": OnboardingAnimation,
  },

  data () {
    return {
      /// UI properties.
      landscapeOrientation: false,
      locationPermission: false,
      camPermission: false,
      blockProgress: false,

      // Geolocation coordinates.
      positionLa: null,
      positionLo: null,
      currentCameraOption: null,

      // Front camera resolution.
      rearCamResolution: {
        width: 1280,
        height: 720,
      },
    };
  },

  mounted () {
    // Check if locationPermission, camPermission en landscape orientation are active.
    this.checkAppOrientation();

    window.addEventListener("resize", this._.debounce(this.checkAppOrientation, 250));

    // @todo If `this.checkAppOrientation = true` go to /client immedietly
  },

  methods: {
    checkAppOrientation () {
      if (window.innerWidth > window.innerHeight) {
        // console.log("orientation = landscape");
        this.landscapeOrientation = !this.landscapeOrientation;
      } else {
        // console.log("orientation = portrait");
        this.landscapeOrientation = false;
      }

      this.checkAllPermission();
    },

    askLocPermission () {
      if (this.blockProgress) return;

      if ("geolocation" in navigator) {
        navigator.geolocation.watchPosition(
          this.updatePosition,
          this.locationAccessDenied,
        );

        this.locationPermission = !this.locationPermission;
      } else {
        console.log("Geolocation is not supported by this browser.");
      }

      this.checkAllPermission();
    },

    locationAccessDenied (error) {
      if (error.code == error.PERMISSION_DENIED) {
        this.locationPermission = false;
        console.log("Geolocation permission was denied.");
        this.goToNextView("/clear-storage");
      }
    },

    updatePosition: function (position) {
      this.positionLa = position.coords.latitude;
      this.positionLo = position.coords.longitude;
    },

    askCamPermission () {
      if (this.blockProgress) return;

      const curScope = this;

      this.currentConstraints = {
        video: {
          facingMode: this.currentCameraOption,
          width: this.rearCamResolution.width,
          height: this.rearCamResolution.height,
        },
        audio: false,
      };

      navigator.mediaDevices
        .getUserMedia(this.currentConstraints)
        .then(mediaStream => {
          // Stop the stream
          const tracks = mediaStream.getTracks();
          tracks[0].stop();
        })
        .then(() => {
          curScope.camPermission = !curScope.camPermission;
        })
        .then(() => {
          curScope.checkAllPermission();
        })
        .catch((err) => {
          console.log("==> Error occured in 'showStream':/ Permission denied");
          console.error(err);
          this.goToNextView("/clear-storage");
        })
      ;
    },

    checkAllPermission () {
      if (
        this.locationPermission &&
        this.camPermission &&
        this.landscapeOrientation
      ) {
        this.goToNextView("/client");
      }
    },

    goToNextView (route) {
      this.blockProgress = true;

      setTimeout(() => {
        this.blockProgress = false;
        this.$router.push(route);
      }, 1000);
    },
  },
};
</script>

<style lang="scss" scoped>
.image-section {
  display: flex;
  align-items: center;
  height: 50%;
}

.text-section {
  display: flex;
  flex-direction: column;
  align-self: center;
  justify-content: space-between;
  padding: 2.5rem 5%;
  height: 50%;

  &-header {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    justify-content: flex-start;
    width: 100%;
    text-align: left;

    .odk-title {
      margin-bottom: 1rem;
    }
  }

  &-buttons {
    .button {
      margin-bottom: .75rem;

      div {
        display: flex;
        align-items: center;
        width: 100%;

        .checkmark {
          width: 1rem;
        }

        .buttonspan-margin {
          margin-left: 1rem;
        }
      }
    }
  }
}

.check-item-complete {
  background: rgba(105, 89, 133, 0.6) !important;
}

.tip {
  margin-top: 0.5rem;
  text-align: left;
  font-size: 0.875rem;
}

@media (orientation: landscape) {
  .image-section {
    width: 50%;
    height: 100%;
    max-height: 414px;
  }

  .text-section {
    width: 50%;
    height: 100%;
    max-height: 414px;
  }
}
</style>
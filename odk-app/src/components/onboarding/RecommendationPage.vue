<template>
  <odk-container>
    <div class="image-section">
      <!-- <div class="image-section-left"> -->
      <img
        class="recommendation-img"
        :class="{ 'is-opaque': step === 0 }"
        src="@/assets/pwa/recommendation1-2.png"
        alt
      >
      <img
        class="recommendation-img"
        :class="{ 'is-opaque': step === 1 }"
        src="@/assets/pwa/recommendation2-2.png"
        alt
      >
      <!-- </div> -->

      <!-- <div class="image-section-right">
        <img
          class="recommendation-img"
          :class="{ 'is-opaque': step === 2 }"
          src="@/assets/pwa/recommendation2.png"
          alt
        >
      </div> -->
    </div>

    <div class="text-section">
      <div class="text-section-header">
        <p class="caption-1">
          {{ content.caption }}
        </p>
        <h1 class="odk-title">
          {{ content.steps[step].title }}
        </h1>
        <p class="body-1">
          {{ content.steps[step].body }}
        </p>
      </div>

      <transition-group
        name="fadeout"
        tag="div"
        class="text-section-buttons"
      >
        <b-button
          ref="buttonNext"
          key="buttonNext"
          type="is-secondary"
          rounded
          class="fadeout-item"
          @click="switchRmd"
        >
          Volgende
        </b-button>

        <router-link
          v-if="step < 1"
          key="buttonSkip"
          to="/checklist"
          tag="b-button"
          class="is-primary is-rounded is-outlined fadeout-item"
        >
          Overslaan
        </router-link>
      </transition-group>
    </div>
  </odk-container>
</template>

<script>
import { checkLoggedIn } from "../../utils/loggedInCheck";

export default {
  name: "RecommendationPage",

  data () {
    return {
      step: 0,
      content: {
        caption: "It is recommended to",
        steps: [
          {
            title: "Charge your phone",
            body: "Streaming consumes a lot of battery.",
          },
          {
            title: "Check your data usage",
            body: "Streaming takes a lot of data. An unlimited subscription is recommended.",
          },
          // {
          //   title: "Choose your own mode",
          //   body: "Manual mode lets you choose when you want to stream. The automatic mode will be able to start and stop the stream based on your driving speed.",
          // },
        ],
      },
    };
  },

  mounted () {
    this.checkUserType();
  },

  methods: {
    switchRmd () {
      this.step >= 1 ? this.$router.push("/checklist") : this.step++;

      this.$refs.buttonNext.$el.focus();

      setTimeout(() => {
        this.$refs.buttonNext.$el.blur();
      }, 250);
    },

    // ----

    checkUserType () {
      const loggedIn = checkLoggedIn();
      if (!loggedIn) {
        this.$router.push("/welcome");
      }
    },
  },
};
</script>

<style lang="scss" scoped>
.image-section {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;

  // &-left {
  //   display: flex;
  //   flex-direction: column;
  //   justify-content: center;
  // }

  // &-right {
  //   display: flex;
  // }

  .recommendation-img {
    position: absolute;
    max-height: 60vh;
    max-width: 60%;
    object-fit: contain;
    opacity: 0.5;
    margin: 1rem;
    display: flex;

    &.is-opaque {
      opacity: 1;
      transition: opacity 350ms ease;
    }

    &:nth-child(1) {
      top: 1rem;
      align-self: flex-start;
    }

    &:nth-child(2) {
      bottom: 1rem;
      align-self: flex-end;
      transform: translateX(1rem);
    }
  }
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
  }

  &-buttons {
    display: flex;
    position: relative;
    flex-direction: column;
    width: 100%;

    .button {
      &:last-of-type {
        margin-top: 1rem;
      }
    }
  }
}

// Transition classes
.fadeout-item {
  transition: all 500ms ease-out;
}

.fadeout-enter,
.fadeout-leave-to {
  opacity: 0;
}

.fadeout-leave-active {
  position: absolute;
  width: 100%;
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

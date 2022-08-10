<template>
  <odk-container>
    <div class="image-section">
      <img src="@/assets/pwa/trial.png" alt>
    </div>

    <div class="text-section">
      <div class="text-section-header">
        <h1 class="odk-title is-4 page-title">
          <router-link to="/welcome">
            <img
              svg-inline
              svg-sprite
              src="@/assets/ui/chevron-left.svg"
              alt="Ga terug"
              class="back-button"
            >
          </router-link>
          ODK uitproberen
        </h1>
        <p class="body-1">
          While trying out the App, your scan results will not be saved. 
          If you have an account, go back and log in with your code.
        </p>
      </div>

      <div class="text-section-buttons">
        <!-- Login -->
        <b-button
          class="is-secondary is-rounded is-expanded"
          @click="toRecommendation()"
        >
          Try it now
        </b-button>
      </div>
    </div>
  </odk-container>
</template>

<script>
import { checkLoggedIn } from "../../utils/loggedInCheck";

export default {
  name: "TrialPage",

  data () {
    return {};
  },

  mounted () {
    this.checkUserType();
  },

  methods: {
    toRecommendation () {
      localStorage.userType = "demo";
      this.$router.push("/recommendation");
    },

    // ----

    checkUserType () {
      const loggedIn = checkLoggedIn();
      if (loggedIn) {
        this.$router.push("/client");
      }
    },
  },
};
</script>

<style lang="scss" scoped>
a::after {
  display: none;
}

.image-section {
  display: flex;
  align-items: center;

  img {
    object-fit: contain;
    max-width: 104%;
    max-height: 95vh;
    margin-left: -8%;
  }
}

.text-section {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-self: center;
  padding: 2.5rem 5%;
  height: 50%;

  &-header {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    justify-content: flex-start;
    margin-top: 1rem;
    width: 100%;
    text-align: left;

    .page-title {
      line-height: 1.2rem;
      display: flex;

      .back-button {
        margin-right: 0.8rem;
        width: 1.25rem;
        height: 1.25rem;
        outline: none;
      }
    }
  }

  &-buttons {
    display: flex;
    flex-direction: column;
    width: 100%;

    .button {
      width: 100%;
    }
  }
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

<template>
  <odk-container>
    <div class="image-section">
      <img src="@/assets/pwa/intro.png" alt>
    </div>

    <div class="text-section">
      <div class="text-section-header">
        <h1 class="odk-title">Object Detection Kit</h1>
        <p class="body-1">Keep the streets clean by scanning while driving</p>
      </div>

      <div class="text-section-buttons">
        <!-- Login -->
        <router-link
          to="/user"
          tag="b-button"
          class="is-secondary is-rounded is-expanded"
        >
          Login
        </router-link>

        <!-- Start trial / Demo user -->
        <b-button
          class="is-primary is-outlined is-rounded is-expanded"
          @click="toTrial()"
        >
          Nu uitproberen
        </b-button>
      </div>
    </div>
  </odk-container>
</template>

<script>
import { checkLoggedIn } from "../../utils/loggedInCheck";
import { startupCheck } from "@/mixins/startupCheck";

export default {
  name: "WelcomePage",

  mixins: [ startupCheck ],

  data () {
    return {};
  },

  mounted () {
    this.checkUserType();
  },

  methods: {
    toTrial () {
      this.$router.push("/trial");
    },

    // ----

    checkUserType () {
      const loggedIn = checkLoggedIn();
      if (loggedIn) {
        this.$router.push("/client");
      } else {
        localStorage.clear();
      }
    },
  },
};
</script>

<style lang="scss" scoped>
.image-section {
  display: flex;
  align-items: center;

  img {
    object-fit: contain;
    max-width: 110%;
    max-height: 95vh;
    margin-left: -10%;
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
  }

  &-buttons {
    display: flex;
    flex-direction: column;
    width: 100%;

    .button {
      width: 100%;

      &:nth-child(1) {
        margin-bottom: 1rem;
      }
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

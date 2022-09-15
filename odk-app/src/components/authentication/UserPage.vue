<template>
  <odk-container>
    <div class="image-section">
      <img src="@/assets/pwa/intro.png" alt>
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
          Login
        </h1>
        <p class="body-1">This login is for ODP-be'ah project.</p>
      </div>

      <div class="text-section-dropdown">
        <b-field label="Scan driver">
          <b-select v-model="chosenUser" class="select" placeholder="Select your ID">
            <option
              v-for="option in users"
              :key="option.id"
              :value="option.name"
            >
              {{ option.name }}
            </option>
          </b-select>
        </b-field>

        <img src="@/assets/pwa/beah-logo.png" alt>
      </div>
    </div>
  </odk-container>
</template>

<script>
import { checkLoggedIn } from "../../utils/loggedInCheck";
import { fetchEndpoint } from "@/utils/fetchEndpoint";

export default {
  name: "UserPage",

  data () {
    return {
      apiHttpUrl: process.env.VUE_APP_API_HTTP_URL,
      chosenUser: null,
      users: [],
    };
  },

  watch: {
    chosenUser (value) {
      if (value != null) {
        // Create values
        const user_name = value;
        let user_email = "";

        // Retreive email where chosen user == user from array
        for (let u = 0; u < this.users.length; u++) {
          const user = this.users[u];
          
          if (user.name == value) {
            user_email = user.email;
            break;
          }
        }

        // Set temporary localStorage values
        localStorage.username = user_name;
        localStorage.email = user_email;

        // Send user to code page, with props
        setTimeout(() => {
          this.$router.push({
            name: "code-page",
            params: { username: user_name, email: user_email },
          });
        }, 200);
      }
    },
  },

  mounted () {
    this.checkUserType();

    // Get list of users
    this.getUsers();
  },

  methods: {
    async getUsers () {
      // Fetch data
      const data = await fetchEndpoint("/users-unauth", "GET", false, false);

      // Check for potential fetch error
      if (data.status && data.status == "error") {
        return;
      }

      // Set data
      data.forEach(user => {
        if (user.full_name != "admin") {
          this.users.push({
            name: user.full_name,
            email: user.email,
          });
        }
      });
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
a::after {
  display: none;
}

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

  &-dropdown {
    width: 100%;
    margin-bottom: 1rem;
    display: flex;
    flex-direction: column;
    align-items: center;

    .field {
      width: 100%;
      text-align: left;

      ::v-deep .label {
        font-weight: 600;
      }

      .control {
        width: 100%;

        &::after {
          display: none;
        }

        ::v-deep span {
          width: 100%;

          &::after {
            border-color: var(--color-dark);
          }

          select {
            width: 100%;
            border: 1px solid rgb(152, 145, 164);

            &:active,
            &:focus {
              box-shadow: none;
            }
          }
        }
      }
    }

    img {
      width: 30%;
      margin-top: 1rem;
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

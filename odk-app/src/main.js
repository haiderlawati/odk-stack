import Vue from 'vue'
import App from './App.vue'
import Buefy from 'buefy'
import Vuelidate from 'vuelidate'
import VueRouter from 'vue-router'
import { routes } from './routes'
import './registerServiceWorker'
import 'buefy/dist/buefy.css'
import VueAwesomeSwiper from 'vue-awesome-swiper'
import 'swiper/dist/css/swiper.css'
import DrawerLayout from 'vue-drawer-layout'
import VieOtpInput from "@bachdgvn/vue-otp-input";

Vue.component("vie-otp-input", VieOtpInput);
export const eventBus = new Vue(); 


// document.cookie = 'cross-site-cookie=bar; SameSite=None';

const router = new VueRouter({
  routes,
  mode: 'history'
});

Vue.config.productionTip = false
Vue.use(DrawerLayout)
Vue.use(Vuelidate)
Vue.use(Buefy)
Vue.use(VueRouter);
Vue.use(VueAwesomeSwiper, /* { default global options } */)

new Vue({
  router,
  render: h => h(App),
}).$mount('#app')
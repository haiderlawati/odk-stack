<template>
  <odk-container>
    <div class="image-section">
      <img src="@/assets/pwa/notification.png" alt>
    </div>

    <div class="text-section">
      <div class="text-section-header">
        <h1 class="odk-title">Verwijder sitegegevens</h1>
        <p class="body-1">You probably have not granted access to use your location and/or camera. Since this app is a PWA, you would have to delete the site data to use the app.</p>
      </div>

      <div class="text-section-footer">
        <router-link :to="{ name:'reset-manual', params: { openCard: 'android' } }">
          How to clear stored data?
        </router-link>
      </div>
    </div>
  </odk-container>
</template>

<script>
export default {
  components: {
    OdkContainer: () => import("@/components/elements/Container.vue"),
  },
};
</script>

<style lang="scss" scoped>
.image-section {
  display: flex;
  align-items: center;

  img {
    object-fit: contain;
    max-width: 105%;
    max-height: 95vh;
    margin-left: -5%;
  }
}

.text-section {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: center;
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

  &-footer {
    width: 100%;
    text-align: left;
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

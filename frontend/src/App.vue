<template>
  <div>
    <router-view />
    <AppUpdatePrompt />
  </div>
</template>

<script>
import AppUpdatePrompt from './components/AppUpdatePrompt.vue'

export default {
  name: 'App',
  components: { AppUpdatePrompt },
}
</script>

<style>
/* global app styles can go here */
</style>

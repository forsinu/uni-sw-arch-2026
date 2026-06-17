<template>
  <div id="app">
    <nav v-if="showNavbar" class="navbar">
      <div class="nav-container">
        <router-link to="/" class="logo">Software Architecture</router-link>
        <ul class="nav-menu">
          <li><router-link to="/">Home</router-link></li>
        </ul>
      </div>
    </nav>
    <router-view />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from './stores/authStore'

const route = useRoute()
const authStore = useAuthStore()

const showNavbar = computed(() => {
  return route.path !== '/login' && route.path !== '/dashboard'
})
</script>

<style scoped>
.navbar {
  background-color: #2c3e50;
  padding: 1rem 0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  color: white;
  font-size: 1.5rem;
  font-weight: bold;
  text-decoration: none;
}

.nav-menu {
  display: flex;
  list-style: none;
  gap: 2rem;
  margin: 0;
  padding: 0;
}

.nav-menu a {
  color: white;
  text-decoration: none;
  transition: color 0.3s;
}

.nav-menu a:hover {
  color: #42b983;
}
</style>

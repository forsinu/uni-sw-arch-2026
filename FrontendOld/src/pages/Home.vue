<template>
  <main class="home">
    <section class="hero">
      <div class="hero-content">
        <h1>Software Architecture 2025/2026</h1>
        <p class="subtitle">Progetto di Architettura del Software</p>
        <div class="hero-buttons">
          <button @click="goToApp" class="btn btn-primary">Accedi all'Applicazione</button>
          <button class="btn btn-secondary">Documentazione</button>
        </div>
      </div>
    </section>

    <section class="features">
      <div class="container">
        <h2>Funzionalità Principali</h2>
        <div class="features-grid">
          <FeatureCard
            icon="🔐"
            title="Autenticazione"
            description="Sistema di autenticazione sicuro e affidabile"
          />
          <FeatureCard
            icon="🏆"
            title="Competizioni"
            description="Gestione completa di competizioni e sfide"
          />
          <FeatureCard
            icon="🌐"
            title="Federazioni"
            description="Sistema di federazione distribuito"
          />
        </div>
      </div>
    </section>

    <section class="info">
      <div class="container">
        <h2>Benvenuto</h2>
        <p>Questa è l'applicazione frontend del progetto di Software Architecture. Utilizza Vue.js 3 con Vite come build tool.</p>
      </div>
    </section>
  </main>
</template>

<script setup>
import { useRouter } from 'vue-router'
import FeatureCard from '../components/FeatureCard.vue'

const router = useRouter()

const goToApp = () => {
  router.push('/login')
}
</script>

<style scoped>
.home {
  min-height: 100vh;
}

.hero {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 6rem 2rem;
  text-align: center;
}

.hero-content h1 {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.subtitle {
  font-size: 1.25rem;
  margin-bottom: 2rem;
  opacity: 0.9;
}

.hero-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.btn {
  padding: 0.75rem 2rem;
  font-size: 1rem;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary {
  background-color: white;
  color: #667eea;
  font-weight: bold;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.2);
}

.btn-secondary {
  background-color: transparent;
  color: white;
  border: 2px solid white;
}

.btn-secondary:hover {
  background-color: white;
  color: #667eea;
}

.features {
  padding: 4rem 2rem;
  background-color: #f5f5f5;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
}

.features h2, .info h2 {
  text-align: center;
  font-size: 2.5rem;
  margin-bottom: 3rem;
  color: #2c3e50;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
}

.info {
  padding: 4rem 2rem;
  text-align: center;
}

.info p {
  font-size: 1.1rem;
  color: #555;
  max-width: 800px;
  margin: 0 auto;
}
</style>

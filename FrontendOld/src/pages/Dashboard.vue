<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1>Dashboard</h1>
      <div class="user-info">
        <span>Benvenuto, {{ authStore.user?.email }}</span>
        <button @click="logout" class="btn-logout">Esci</button>
      </div>
    </div>

    <div class="container">
      <div class="actions-grid">
        <ActionCard
          icon="👥"
          title="Gestisci Team"
          description="Visualizza e gestisci i team di nuoto"
          @click="navigateTo('teams')"
        />
        <ActionCard
          icon="🏆"
          title="Competizioni"
          description="Visualizza gare e risultati"
          @click="navigateTo('competitions')"
        />
        <ActionCard
          icon="🎯"
          title="Iscrizioni"
          description="Iscriviti a gare e competizioni"
          @click="navigateTo('entries')"
        />
        <ActionCard
          icon="🏊"
          title="Atleti"
          description="Gestisci atleti e federazione"
          @click="navigateTo('athletes')"
        />
      </div>

      <div class="sections">
        <section v-show="currentView === 'teams'" class="section">
          <h2>Team di Nuoto</h2>
          <TeamsList :authStore="authStore" />
        </section>

        <section v-show="currentView === 'competitions'" class="section">
          <h2>Competizioni</h2>
          <CompetitionsList :authStore="authStore" />
        </section>

        <section v-show="currentView === 'entries'" class="section">
          <h2>Iscrizioni Gare</h2>
          <EntriesList :authStore="authStore" />
        </section>

        <section v-show="currentView === 'athletes'" class="section">
          <h2>Atleti</h2>
          <AthletesList :authStore="authStore" />
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/authStore'
import ActionCard from '../components/ActionCard.vue'
import TeamsList from '../components/TeamsList.vue'
import CompetitionsList from '../components/CompetitionsList.vue'
import EntriesList from '../components/EntriesList.vue'
import AthletesList from '../components/AthletesList.vue'

const authStore = useAuthStore()
const router = useRouter()
const currentView = ref('teams')

const navigateTo = (view) => {
  currentView.value = view
}

const logout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.dashboard-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dashboard-header h1 {
  margin: 0;
}

.user-info {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.btn-logout {
  background-color: rgba(255, 255, 255, 0.2);
  border: 1px solid white;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-logout:hover {
  background-color: rgba(255, 255, 255, 0.3);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.sections {
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  padding: 2rem;
}

.section {
  animation: fadeIn 0.3s ease-in;
}

.section h2 {
  color: #2c3e50;
  margin-bottom: 1.5rem;
  border-bottom: 2px solid #667eea;
  padding-bottom: 0.5rem;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>

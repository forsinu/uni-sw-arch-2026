<template>
  <div>
    <div v-if="loading" class="loading">Caricamento...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="teams.length === 0" class="empty">Nessun team trovato</div>
    <div v-else class="table-container">
      <table class="table">
        <thead>
          <tr>
            <th>Nome</th>
            <th>Nome Breve</th>
            <th>Stato</th>
            <th>Azioni</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="team in teams" :key="team.id">
            <td>{{ team.name }}</td>
            <td>{{ team.shortName }}</td>
            <td>
              <span :class="['badge', team.isActive ? 'active' : 'inactive']">
                {{ team.isActive ? 'Attivo' : 'Inattivo' }}
              </span>
            </td>
            <td>
              <button @click="viewDetails(team)" class="btn-small">Dettagli</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'

const props = defineProps({
  authStore: Object
})

const teams = ref([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const response = await api.get('/v1/team?limit=50')
    teams.value = response.data.teams || []
  } catch (err) {
    error.value = 'Errore nel caricamento dei team'
    console.error(err)
  } finally {
    loading.value = false
  }
})

const viewDetails = (team) => {
  console.log('Team details:', team)
}
</script>

<style scoped>
.loading,
.error,
.empty {
  padding: 2rem;
  text-align: center;
  background: #f5f5f5;
  border-radius: 5px;
}

.error {
  background: #fee;
  color: #c33;
}

.empty {
  color: #666;
}

.table-container {
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
}

.table th {
  background-color: #667eea;
  color: white;
  padding: 1rem;
  text-align: left;
  font-weight: bold;
}

.table td {
  padding: 1rem;
  border-bottom: 1px solid #ddd;
}

.table tbody tr:hover {
  background-color: #f9f9f9;
}

.badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: bold;
}

.badge.active {
  background-color: #d4edda;
  color: #155724;
}

.badge.inactive {
  background-color: #f8d7da;
  color: #721c24;
}

.btn-small {
  padding: 0.5rem 1rem;
  background-color: #667eea;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 0.85rem;
}

.btn-small:hover {
  background-color: #5568d3;
}
</style>

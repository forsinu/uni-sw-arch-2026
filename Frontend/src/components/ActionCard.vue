<template>
  <div class="action-card" @click="$emit('click')">
    <div class="icon">{{ icon }}</div>
    <h3>{{ title }}</h3>
    <p>{{ description }}</p>
  </div>
</template>

<script setup>
defineProps({
  icon: String,
  title: String,
  description: String
})

defineEmits(['click'])
</script>

<style scoped>
.action-card {
  background: white;
  padding: 1.5rem;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s;
  text-align: center;
}

.action-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 20px rgba(102, 126, 234, 0.3);
}

.icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

h3 {
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

p {
  color: #666;
  font-size: 0.9rem;
}
</style>

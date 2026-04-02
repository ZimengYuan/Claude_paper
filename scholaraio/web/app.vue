<template>
  <div class="min-h-screen bg-gray-50">
    <nav class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex min-h-16 flex-col justify-center gap-2 py-3 md:h-16 md:flex-row md:items-center md:justify-between md:py-0">
          <div class="flex items-center">
            <div>
              <NuxtLink to="/" class="text-xl font-bold text-gray-900">ScholarAIO</NuxtLink>
              <p class="text-xs text-gray-500">GitHub Pages read-only snapshot</p>
            </div>
            <div class="ml-6 flex flex-wrap gap-2 md:ml-10 md:space-x-4">
              <NuxtLink to="/" class="px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100" :class="{ 'bg-gray-100': route.path === '/' }">Library</NuxtLink>
              <NuxtLink to="/explore" class="px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100" :class="{ 'bg-gray-100': route.path.startsWith('/explore') }">Explore</NuxtLink>
              <NuxtLink to="/knowledge" class="px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100" :class="{ 'bg-gray-100': route.path === '/knowledge' }">Knowledge</NuxtLink>
              <NuxtLink to="/graph" class="px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100" :class="{ 'bg-gray-100': route.path === '/graph' }">Graph</NuxtLink>
            </div>
          </div>
          <div class="text-xs text-gray-500">Static export from local `data/papers`</div>
        </div>
      </div>
    </nav>
    <main>
      <NuxtPage />
    </main>
  </div>
</template>

<script setup>
const route = useRoute()
</script>

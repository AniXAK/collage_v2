import { createRouter, createWebHistory } from 'vue-router'
import { createApp } from 'vue'
import './style.css'
import App from './App.vue'


import Default from './components/default.vue'
import Download from './components/download.vue'
import Result from './components/result.vue'

const router = createRouter ({
    history: createWebHistory(),
    routes: [{
        name: 'default',
        path: '/',
        component: Default
    },{
        name: 'download',
        path: '/download',
        component: Download  
    },{
        name: 'result',
        path: '/result',
        component: Result
    }]
})
createApp(App)
  .use(router)
  .mount('#app')

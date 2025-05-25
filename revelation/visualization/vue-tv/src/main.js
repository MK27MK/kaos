import { createApp } from "vue";
// root component imported from a SFC
import App from "./App.vue";

const app = createApp(App);
app.mount("#app"); // returns the root component instance

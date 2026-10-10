import DefaultTheme from "vitepress/theme";
import type { Theme } from "vitepress";
import StoreSourceCard from "./components/StoreSourceCard.vue";
import "./custom.css";

export default {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    app.component("StoreSourceCard", StoreSourceCard);
  }
} satisfies Theme;

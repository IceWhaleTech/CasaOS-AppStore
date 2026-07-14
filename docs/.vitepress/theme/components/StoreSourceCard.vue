<script setup lang="ts">
import { computed, ref } from "vue";

const props = withDefaults(
  defineProps<{
    title: string;
    url: string;
    summary: string;
    maintainer?: string;
    status?: string;
    tags?: string;
    copyLabel?: string;
    copiedLabel?: string;
    openLabel?: string;
  }>(),
  {
    maintainer: "",
    status: "",
    tags: "",
    copyLabel: "Copy Link",
    copiedLabel: "Copied",
    openLabel: "Open"
  }
);

const copied = ref(false);

const tagList = computed(() =>
  props.tags
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean)
);

async function copyUrl() {
  try {
    await navigator.clipboard.writeText(props.url);
    copied.value = true;
    window.setTimeout(() => {
      copied.value = false;
    }, 1600);
  } catch {
    copied.value = false;
  }
}
</script>

<template>
  <article class="store-source-card">
    <div class="store-source-card__head">
      <div>
        <h3>{{ title }}</h3>
        <p>{{ summary }}</p>
      </div>
      <span v-if="status" class="store-source-card__status">{{ status }}</span>
    </div>

    <div class="store-source-card__meta">
      <span v-if="maintainer">Maintainer: {{ maintainer }}</span>
      <div v-if="tagList.length" class="store-source-card__tags">
        <span v-for="tag in tagList" :key="tag" class="store-source-card__tag">{{ tag }}</span>
      </div>
    </div>

    <div class="store-source-card__url">
      <code>{{ url }}</code>
    </div>

    <div class="store-source-card__actions">
      <button type="button" class="store-source-card__button store-source-card__button--brand" @click="copyUrl">
        {{ copied ? copiedLabel : copyLabel }}
      </button>
      <a class="store-source-card__button store-source-card__button--ghost" :href="url" target="_blank" rel="noreferrer">
        {{ openLabel }}
      </a>
    </div>
  </article>
</template>

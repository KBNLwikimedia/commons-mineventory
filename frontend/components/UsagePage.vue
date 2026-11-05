<!-- /verbruik: paid calls today, per day and the log (functional design 6.4, 8.3). -->
<template>
  <div class="cc-verbruik">
    <template v-if="data">
      <section class="cc-tegels">
        <div class="cc-tegel">
          <span>{{ t("usage.today") }}</span>
          <strong>{{ data.vandaag.gebruikt_vandaag }} / {{ data.vandaag.daglimiet }}</strong>
        </div>
        <div class="cc-tegel">
          <span>{{ t("usage.cost_today") }}</span>
          <strong>{{ money(data.vandaag.kosten_vandaag_usd, language) }} / {{ money(data.vandaag.dagbudget_usd, language) }}</strong>
        </div>
        <div class="cc-tegel">
          <span>{{ t("usage.total") }}</span>
          <strong>{{ data.totaal.aanroepen }} · {{ money(data.totaal.kosten_usd, language) }}</strong>
        </div>
      </section>
      <p v-if="!data.logboek.length" class="cc-leeg">{{ t("usage.empty") }}</p>
      <table v-else class="cc-tabel">
        <thead>
          <tr>
            <th>{{ t("usage.time") }}</th>
            <th>{{ t("usage.kind") }}</th>
            <th>{{ t("usage.file") }}</th>
            <th>{{ t("usage.term") }}</th>
            <th>{{ t("usage.user") }}</th>
            <th class="getal">{{ t("usage.cost") }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(entry, i) in data.logboek" :key="i">
            <td>{{ entry.tijd.replace("T", " ") }}</td>
            <td>{{ t(`usage.kind_${entry.soort || "sam"}`) }}</td>
            <td><a v-if="entry.bestand" :href="`/?mid=${entry.bestand}&pagina=${entry.pagina || 1}`">{{ entry.titel || entry.bestand }}</a></td>
            <!-- SAM: the search term; an AI description: its model (and the part asked anew). -->
            <td>{{ (entry.soort || "sam") === "sam" ? entry.term : [entry.deel && t(`usage.part_${entry.deel}`), entry.model].filter(Boolean).join(" · ") || entry.term }}</td>
            <td>{{ entry.gebruiker || "—" }}</td>
            <td class="getal">{{ money(entry.kosten_usd, language) }}</td>
          </tr>
        </tbody>
      </table>
    </template>
    <cdx-message v-if="error" type="error">{{ error }}</cdx-message>
  </div>
</template>

<script setup>
import { inject, onMounted, ref } from "vue";
import { CdxMessage } from "@wikimedia/codex";
import { API, errorText, get } from "../api.js";
import { money, useT } from "../i18n.js";

const t = useT();
const language = inject("language", "nl");
const data = ref(null);
const error = ref("");

onMounted(async () => {
  try {
    data.value = await get(`${API}/verbruik`);
  } catch (e) {
    error.value = errorText(t, e);
  }
});
</script>

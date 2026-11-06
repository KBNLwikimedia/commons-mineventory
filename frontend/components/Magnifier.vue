<!--
  The magnifier (functional design 10.4): the cut-out, "Wat staat hierop?",
  the caption and the Commons concept, in tabs.
-->
<template>
  <cdx-dialog
    :open="open"
    class="cc-vergroter"
    :title="name"
    :use-close-button="true"
    :close-button-label="t('actions.close')"
    @update:open="emit('update:open', $event)"
  >
    <!-- Own header (the Codex classes), so the subtitle can link to the original on Commons, on every tab. -->
    <template #header>
      <div class="cdx-dialog__header__title-group">
        <h2 class="cdx-dialog__header__title">{{ listName || name }}</h2>
        <p class="cdx-dialog__header__subtitle">
          {{ subtitle }}
          <template v-if="file.url">
            · {{ t("objects.source_file") }}
            <a :href="file.url" target="_blank" rel="noopener">{{ file.naam || fileName(file.titel) }}</a>
            <cdx-icon :icon="cdxIconLinkExternal" size="x-small" />
          </template>
        </p>
      </div>
      <!-- Previous and next object, in the order of the list "Gevonden objecten (uitsneden)" (also ← and →). -->
      <span v-if="position.total > 1" class="cc-vergroter-nav" role="group" :aria-label="t('magnifier.nav')">
        <cdx-button weight="quiet" type="button" :disabled="position.index <= 1" :aria-label="t('magnifier.previous')" :title="t('magnifier.previous')" @click="step(-1)">
          <cdx-icon :icon="cdxIconPrevious" />
        </cdx-button>
        <span class="cc-klein">{{ t("magnifier.position", { n: position.index, total: position.total }) }}</span>
        <cdx-button weight="quiet" type="button" :disabled="position.index >= position.total" :aria-label="t('magnifier.next')" :title="t('magnifier.next')" @click="step(1)">
          <cdx-icon :icon="cdxIconNext" />
        </cdx-button>
      </span>
      <cdx-button
        class="cdx-dialog__header__close-button"
        weight="quiet"
        type="button"
        :aria-label="t('actions.close')"
        @click="emit('update:open', false)"
      >
        <cdx-icon :icon="cdxIconClose" />
      </cdx-button>
    </template>
    <cdx-tabs v-model:active="tab" :framed="true">
      <cdx-tab name="uitsnede" :label="t('magnifier.cutout')">
        <div v-if="object.masker" class="cc-weergave">
          <cdx-toggle-button-group v-model="view" :buttons="views" :aria-label="t('magnifier.view')" />
          <span class="cc-klein">{{ t(`concept.format_${view}`) }}</span>
        </div>
        <!-- While the cut-out is made (from a large original this can take a while): a progress bar and a text. -->
        <div class="cc-vergroter-beeld" :class="{ 'cc-laden': imageState === 'loading' }" :aria-busy="imageState === 'loading' ? 'true' : 'false'">
          <div v-if="imageState === 'loading'" class="cc-beeld-laden" role="status">
            <cdx-progress-bar :inline="true" :aria-label="t('magnifier.loading')" />
            <p class="cc-klein">{{ t("magnifier.loading") }}</p>
          </div>
          <cdx-message v-else-if="imageState === 'error'" type="error" :inline="true">{{ t("magnifier.load_error") }}</cdx-message>
          <zoom-image
            v-show="imageState !== 'error'"
            :class="{ 'cc-onzichtbaar': imageState === 'loading' }"
            :src="imageUrl"
            :width="object.box.w"
            :height="object.box.h"
            :alt="name"
            @load="imageState = 'loaded'"
            @error="imageState = 'error'"
          />
        </div>
        <dl class="cc-gegevens">
          <dt>{{ t("magnifier.source") }}</dt>
          <dd>{{ t(`source.${object.bron}`) }}<template v-if="groupNames">: {{ groupNames }}</template> <ai-badge v-if="object.bron === 'sam'" kind="detectie" :model="object.herkomst?.model || config.sam_model" :score="object.score" /><template v-if="object.wikidata"> · <a :href="`https://www.wikidata.org/wiki/${object.wikidata}`" target="_blank" rel="noopener">{{ object.wikidata }}</a></template></dd>
          <dt>{{ t("magnifier.box") }}</dt>
          <dd>{{ object.box.x }}, {{ object.box.y }} · {{ object.box.w }} × {{ object.box.h }} px</dd>
          <template v-if="savedInfo">
            <dt>{{ t("magnifier.saved") }}</dt>
            <dd><saved-label :object="object" /> <retention-info /><br /><span class="cc-klein">{{ savedInfo.title }}</span></dd>
          </template>
          <template v-if="object.herkomst?.p2677"><dt>P2677</dt><dd><code>{{ object.herkomst.p2677 }}</code></dd></template>
          <dt>{{ t("magnifier.caption") }}</dt>
          <dd class="cc-bijschrift">
            <span class="cc-invoer-met-knop" :class="{ 'met-tekstknop': removedCaption && !caption }">
              <cdx-text-input
                v-model="caption"
                :aria-label="t('magnifier.caption')"
                :placeholder="removedCaption ? t('magnifier.caption_removed', { text: removedCaption }) : t('magnifier.caption_placeholder')"
                :title="t('magnifier.caption_placeholder')"
              />
              <cdx-button
                v-if="removedCaption && !caption"
                class="cc-invoer-knop cc-invoer-knop-tekst"
                weight="quiet"
                size="small"
                action="progressive"
                @click="undoRemoveCaption"
              >
                ↶ {{ t("magnifier.undo") }}
              </cdx-button>
              <cdx-button
                v-else-if="caption || object.bijschrift?.tekst"
                class="cc-invoer-knop"
                weight="quiet"
                size="small"
                action="destructive"
                :aria-label="t('magnifier.caption_remove')"
                :title="t('magnifier.caption_remove')"
                @click="removeCaption"
              >
                <cdx-icon :icon="cdxIconTrash" size="small" />
              </cdx-button>
            </span>
            <cdx-button action="progressive" size="small" :disabled="caption === (object.bijschrift?.tekst || '')" @click="saveCaption">{{ t("actions.save_short") }}</cdx-button>
          </dd>
        </dl>
        <div class="cc-knoppen">
          <span class="cc-knopgroep" role="group" :aria-label="t('magnifier.download')">
            <span class="cc-klein">{{ t("magnifier.download") }}</span>
            <cdx-button action="progressive" @click="download('jpg')"><cdx-icon :icon="cdxIconDownload" /> JPG</cdx-button>
            <cdx-button action="progressive" @click="download('png')"><cdx-icon :icon="cdxIconDownload" /> PNG</cdx-button>
          </span>
          <span class="cc-knopgroep" role="group" :aria-label="t('magnifier.view_full')">
            <span class="cc-klein">{{ t("magnifier.view_full") }}</span>
            <cdx-button action="progressive" weight="quiet" @click="viewFull('jpg')"><cdx-icon :icon="cdxIconLinkExternal" /> JPG</cdx-button>
            <cdx-button action="progressive" weight="quiet" @click="viewFull('png')"><cdx-icon :icon="cdxIconLinkExternal" /> PNG</cdx-button>
          </span>
          <!-- No shape yet (a rectangle): the AI image detection finds the outline, for a transparent PNG. -->
          <cdx-button action="progressive" v-if="!object.masker" :title="t('magnifier.refine_mask_help')" @click="emit('refine', object)">
            {{ t("magnifier.refine_mask", { cost: config.betaald ? money(config.sam_usd, config.taal) : t("panel.free").replace(/[()]/g, "") }) }}
          </cdx-button>
          <!-- Fill in what is missing (Muse Image): invented by AI, kept apart from the cut-out (7.7). -->
          <!-- Only the first time; asking again is on the AI-completed tab (wish Olaf). -->
          <cdx-button v-if="!object.aangevuld && !completionHistory.length" action="progressive" :disabled="completing" :title="t('completion.help')" @click="complete">
            {{ t("completion.make") }} <span class="cc-kosten">{{ completionCost }}</span>
          </cdx-button>
          <cdx-button action="destructive" @click="emit('trashed', object.id)"><cdx-icon :icon="cdxIconTrash" /> {{ t("objects.trash") }}</cdx-button>
        </div>
        <busy-note v-if="completing" :message="t('completion.busy')" />
        <cdx-message v-if="completionError" type="error" :inline="true">{{ completionError }}</cdx-message>
      </cdx-tab>

      <!-- The AI-completed version (7.7): its own tab, only when there is one. Never a source,
           never to Commons as a cut-out. A switch shows what the AI filled in. -->
      <cdx-tab v-if="object.aangevuld || completionHistory.length" name="aangevuld" :label="t('completion.tab')">
        <section class="cc-aanvulling">
          <template v-if="!object.aangevuld">
            <p class="cc-uitleg">{{ t("completion.none_current") }}</p>
            <cdx-button action="progressive" :disabled="completing" :title="t('completion.help')" @click="complete">
              {{ t("completion.again") }} <span class="cc-kosten">{{ completionCost }}</span>
            </cdx-button>
          </template>
          <template v-else>
          <h4>{{ t("completion.title") }} <ai-badge kind="aanvulling" :model="object.aangevuld.model" /></h4>
          <cdx-message type="warning" :inline="true">{{ t("completion.warning") }}</cdx-message>
          <cdx-toggle-switch v-model="showFilled" class="cc-aanvulling-schakelaar">{{ t("completion.show_filled") }}</cdx-toggle-switch>
          <div class="cc-vergroter-beeld">
            <zoom-image
              :src="`${base}/aangevuld.png?v=${object.aangevuld.sleutel}`"
              :width="object.aangevuld.afmetingen?.[0] || object.box.w"
              :height="object.aangevuld.afmetingen?.[1] || object.box.h"
              :alt="t('completion.title')"
              :overlay="showFilled ? `${base}/aangevuld-ingevuld.png?v=${object.aangevuld.sleutel}` : ''"
            />
          </div>
          <p v-if="showFilled" class="cc-uitleg"><span class="cc-aanvulling-staal"></span> {{ t("completion.filled_help") }}</p>
          <dl class="cc-gegevens">
            <dt>{{ t("magnifier.source") }}</dt>
            <dd>{{ t("completion.source") }} <ai-badge kind="aanvulling" :model="object.aangevuld.model" /></dd>
            <dt>{{ t("completion.resolution") }}</dt>
            <dd>
              {{ (object.aangevuld.afmetingen || []).join(" × ") }} px
              <span class="cc-klein">{{ t("completion.cutout_size", { size: `${Math.round(object.box.w)} × ${Math.round(object.box.h)}` }) }}</span>
            </dd>
            <dt>{{ t("describe.group_prompt") }}</dt>
            <dd class="cc-groep-prompt">
              <!-- The prompt, with a pencil to change it for the next question (wish Olaf). -->
              <template v-if="!editingPrompt">
                <em><template v-for="(part, i) in completionPrompt" :key="i"><span v-if="part.pill" class="cc-groep-pillen"><cdx-info-chip>{{ part.text }}</cdx-info-chip></span><template v-else>{{ part.text }}</template></template></em>
                <span v-if="object.aangevuld.prompt_eigen" class="cc-klein"> ({{ t("completion.prompt_own") }})</span>
                <cdx-button action="progressive" weight="quiet" size="small" :aria-label="t('completion.prompt_edit')" :title="t('completion.prompt_edit')" @click="startPrompt">
                  <cdx-icon :icon="cdxIconEdit" size="small" />
                </cdx-button>
              </template>
              <template v-else>
                <cdx-text-area v-model="promptDraft" :rows="5" :aria-label="t('completion.prompt_edit')" />
                <p class="cc-klein">
                  {{ t("completion.prompt_edit_help") }}
                  <button type="button" class="cc-link" @click="resetPrompt">{{ t("completion.prompt_default") }}</button>
                  · <button type="button" class="cc-link" @click="editingPrompt = false">{{ t("actions.cancel") }}</button>
                </p>
              </template>
            </dd>
          </dl>
          <p class="cc-uitleg">{{ t("completion.after") }}</p>
          <div class="cc-knoppen">
            <cdx-button action="progressive" @click="downloadCompletion"><cdx-icon :icon="cdxIconDownload" /> PNG</cdx-button>
            <cdx-button action="progressive" weight="quiet" @click="viewCompletion"><cdx-icon :icon="cdxIconLinkExternal" /> {{ t("completion.view") }}</cdx-button>
            <cdx-button action="progressive" :disabled="completing" @click="complete">
              {{ t("completion.again") }} <span class="cc-kosten">{{ completionCost }}</span>
            </cdx-button>
            <cdx-button action="destructive" weight="quiet" @click="forgetCompletion"><cdx-icon :icon="cdxIconTrash" /> {{ t("completion.remove") }}</cdx-button>
          </div>
          </template>
          <busy-note v-if="completing" :message="t('completion.busy')" />
          <cdx-message v-if="completionError" type="error" :inline="true">{{ completionError }}</cdx-message>
          <!-- Earlier versions, one at a time, with their prompt: use one again (free, from
               the cache) or remove it, as with the descriptions (wish Olaf). -->
          <template v-if="completionHistory.length">
            <h4 class="cc-commons-kop">{{ t("completion.history", { n: completionHistory.length }) }}</h4>
            <version-carousel :items="completionHistory" item-key="sleutel" :label="t('completion.history_short')">
              <template #default="{ item: entry }">
                <div class="cc-aanvulling-versie">
                  <img :src="`${base}/aangevuld.png?sleutel=${entry.sleutel}`" alt="" loading="lazy" @error="(e) => (e.target.style.visibility = 'hidden')" />
                  <div>
                    <em class="cc-klein">{{ entry.prompt }}</em>
                    <div class="cc-klein">{{ formatTime(entry.tijdstempel) }}<template v-if="entry.prompt_eigen"> · {{ t("completion.prompt_own") }}</template></div>
                  </div>
                </div>
              </template>
              <template #actions="{ item: entry }">
                <cdx-button action="progressive" size="small" :disabled="completing" @click="useCompletion(entry)">{{ t("describe.history_use") }}</cdx-button>
                <cdx-button action="destructive" weight="quiet" size="small" :disabled="completing" :aria-label="t('describe.history_delete')" :title="t('describe.history_delete')" @click="deleteCompletion(entry)">
                  <cdx-icon :icon="cdxIconTrash" size="small" />
                </cdx-button>
              </template>
            </version-carousel>
          </template>
        </section>
      </cdx-tab>

      <cdx-tab name="beschrijving" :label="t('describe.title')">
        <!--
          One flow for the first and every later question:
          1. the answer (or, before the first one, what you get), with its own actions;
          2. the button that asks the AI, with the cost;
          3. folded away: AI modifiers, earlier descriptions, model and cost.
        -->

        <!-- Step 1 on the left; on the right the cut-out as the AI sees it (red frame, chosen space). -->
        <div class="cc-concept-kop">
        <div class="cc-concept-links">
        <!-- 1a. Before the first answer: what the AI will do, and the caption that goes along. -->
        <section v-if="!description" class="cc-uitleg-vooraf">
          <p>{{ t("describe.intro") }}</p>
          <p>{{ t("describe.intro_modifiers") }}</p>
          <p v-if="object.bijschrift?.tekst" class="cc-klein">
            {{ t("magnifier.caption") }}: <strong>{{ object.bijschrift.tekst }}</strong> — {{ t("describe.caption_goes_along") }}
          </p>
        </section>

        <!-- 1b. The answer. -->
        <section v-else class="cc-antwoord">
          <dl class="cc-gegevens">
            <dt>{{ t("describe.kind") }} <ai-badge kind="soort" :model="description.model" /></dt>
            <dd>{{ fixedValue("kind", description.soort) }} · {{ t("describe.certainty") }}: {{ fixedValue("certainty", description.zekerheid) }}</dd>
            <!-- Each text has its own pencil: edit it in place, with Opslaan and Annuleren. -->
            <template v-for="group in TEXT_GROUPS" :key="group.key">
              <template v-if="group.always || group.fields.some((f) => description[f]) || editingGroup === group.key">
                <dt>
                  {{ t(group.label) }}
                  <ai-badge v-if="group.ai" :model="description.model" :edited="group.fields.some((f) => aiEdited(f))" />
                </dt>
                <dd v-if="editingGroup === group.key" ref="editBox" class="cc-veld-bewerken">
                  <template v-for="field in group.fields" :key="field">
                    <!-- A label only for the NL/EN pairs; a single field has its label on the left. -->
                    <cdx-field :hide-label="group.fields.length === 1">
                      <template #label>{{ t(`describe.field_${field}`) }}</template>
                      <cdx-text-area v-if="group.long" v-model="fieldDraft[field]" :autosize="true" @keydown.esc.stop.prevent="cancelEditing" />
                      <cdx-text-input v-else v-model="fieldDraft[field]" @keydown.esc.stop.prevent="cancelEditing" @keydown.enter="saveEditing" />
                    </cdx-field>
                  </template>
                  <div class="cc-knoppen">
                    <cdx-button action="progressive" weight="primary" :disabled="!fieldChanged" @click="saveEditing">{{ t("actions.save_short") }}</cdx-button>
                    <cdx-button @click="cancelEditing">{{ t("actions.cancel") }}</cdx-button>
                  </div>
                </dd>
                <dd v-else :class="{ 'cc-gelezen-tekst': group.read }">
                  <template v-if="group.fields.length === 2">{{ description[group.fields[0]] }}<br /><i>{{ description[group.fields[1]] }}</i></template>
                  <template v-else>{{ description[group.fields[0]] }}</template>
                  <!-- The pencil after the text: edit this field in place. -->
                  <cdx-button
                    class="cc-veld-potlood"
                    weight="quiet"
                    action="progressive"
                    size="small"
                    :disabled="busy"
                    :aria-label="`${t('lightbox.edit')}: ${t(group.label)}`"
                    :title="`${t('lightbox.edit')}: ${t(group.label)}`"
                    @click="startEditing(group)"
                  >
                    <cdx-icon :icon="cdxIconEdit" size="small" />
                  </cdx-button>
                  <!-- Legible text read by the AI can also be removed with the bin. -->
                  <cdx-button
                    v-if="group.read"
                    weight="quiet"
                    size="small"
                    action="destructive"
                    :disabled="busy"
                    :aria-label="t('describe.remove_text')"
                    :title="t('describe.remove_text')"
                    @click="saveTexts({ [group.fields[0]]: '' })"
                  >
                    <cdx-icon :icon="cdxIconTrash" size="small" />
                  </cdx-button>
                </dd>
              </template>
            </template>
          </dl>

          <!-- What you can do with this answer: undo, go back to the AI text, or remove it. -->
          <div class="cc-knoppen cc-tekst-acties">
            <template v-if="description.bewerkt">
              <cdx-info-chip>{{ t("describe.edited") }}</cdx-info-chip>
              <button type="button" class="cc-link" @click="backToAi">{{ t("describe.back_to_ai") }}</button>
            </template>
            <span v-if="undoTexts" class="cc-klein">
              {{ t("describe.saved_edit") }}
              <button type="button" class="cc-link" @click="undoEdit">↶ {{ t("magnifier.undo") }}</button>
            </span>
            <cdx-button class="cc-rechts-uitlijnen" size="small" weight="quiet" action="destructive" :disabled="busy" @click="removeDescription">
              <cdx-icon :icon="cdxIconTrash" size="small" /> {{ t("describe.remove") }}
            </cdx-button>
          </div>
        </section>
        </div>
        <!-- The image moves to the AI modifiers while they are open, beside the slider (see glidePreview). -->
        <cutout-preview v-if="!previewInModifiers" class="cc-ai-voorbeeld" :src="modelInputUrl" :caption="t('describe.model_sees')" :large="largeInputUrl" :lightbox-title="name" :texts="readTexts" @save-text="saveTexts({ [$event.key]: $event.value })" />
        </div>

        <!-- A group: the prompt the app adds itself to every question about it (7.4). -->
        <dl v-if="groupNames" class="cc-gegevens cc-groep-opdracht">
          <dt>{{ t("describe.group_prompt") }}</dt>
          <dd class="cc-groep-prompt">
            <!-- On: the AI looks at the members only (with space around: the surroundings as context). -->
            <cdx-toggle-switch v-model="groupOnly" class="cc-groep-schakelaar">{{ t("describe.group_only") }}</cdx-toggle-switch>
            <template v-if="groupOnly">
            <em>{{ groupFocus[0] }}<span class="cc-groep-pillen"><cdx-info-chip v-for="(member, i) in groupMemberNames" :key="i">{{ member }}</cdx-info-chip></span>{{ groupFocus[1] }}</em>
            <!-- What the members were described as before, alone: goes along as context. -->
            <template v-if="groupContext.length">
              <br /><em>{{ t("describe.group_context") }}</em>
              <ul class="cc-groep-context">
                <li v-for="(member, i) in groupContext" :key="i">
                  <cdx-info-chip>{{ member.name }}</cdx-info-chip> <em>{{ member.text }}</em>
                  <em v-if="member.inText"> {{ t("describe.group_context_in") }}: “{{ member.inText }}”.</em>
                  <em v-if="member.around"> {{ t("describe.group_context_around") }}: “{{ member.around }}”.</em>
                </li>
              </ul>
            </template>
            </template>
            <span v-else class="cc-uitleg">{{ t("describe.group_off") }}</span>
            <br /><span class="cc-uitleg">{{ t("describe.group_prompt_help") }}</span></dd>
        </dl>

        <!-- 2. AI modifiers: steer the next question (hint, and the space around the cut-out). -->
        <cdx-accordion v-model="openModifiers" class="cc-beschrijving-blok" @cc-closing="previewInModifiers = false">
          <template #title>{{ t("describe.modifiers") }}</template>
          <template #description>{{ modifiersSummary || t("describe.modifiers_default") }}</template>
          <p class="cc-klein">{{ t("describe.modifiers_help") }}</p>
          <div class="cc-concept-kop cc-ai-sturing">
            <div class="cc-concept-links">
              <!-- An optional hint, e.g. "only the boy"; not the caption, not for Commons. -->
              <cdx-field class="cc-aanwijzing">
                <template #label>{{ t("describe.hint") }}</template>
                <template #help-text>{{ t("describe.hint_help") }}</template>
                <cdx-text-input v-model="hint" :placeholder="t('describe.hint_placeholder')" :maxlength="300" @keydown.enter="describe(Boolean(description))" />
              </cdx-field>
              <!-- How long the description is, as for the whole image (wish Olaf), with the Commons caption stop. -->
              <detail-slider v-model="descLevel" :disabled="busy" :levels="OBJECT_DESCRIPTION_LEVELS" prefix="objdetail" />
              <label class="cc-marge">
                <span>{{ t("describe.margin", { pct: Math.round(margin * 100) }) }}</span>
                <input v-model.number="margin" type="range" min="0" max="1" step="0.05" :aria-label="t('describe.margin_label')" />
                <span class="cc-klein">{{ t("describe.margin_help") }}</span>
              </label>
            </div>
            <cutout-preview v-if="previewInModifiers" class="cc-ai-voorbeeld" :src="modelInputUrl" :caption="t('describe.model_sees')" :large="largeInputUrl" :lightbox-title="name" :texts="readTexts" @save-text="saveTexts({ [$event.key]: $event.value })" />
          </div>
        </cdx-accordion>

        <!-- 3. Ask the AI, under the modifiers that steer it: the first time it is the main action. -->
        <div class="cc-vraag-knop">
          <cdx-button action="progressive" :weight="description ? 'normal' : 'primary'" :disabled="busy" @click="describe(Boolean(description))">
            {{ description ? t("describe.again") : t("describe.ask") }} <span class="cc-kosten">{{ costLabel }}</span>
          </cdx-button>
          <span v-if="modifiersSummary" class="cc-klein">{{ t("describe.with_modifiers", { what: modifiersSummary }) }}</span>
        </div>
        <div v-if="busy" class="cc-bezig" role="status">
          <cdx-progress-bar :inline="true" :aria-label="t('describe.busy', { seconds })" />
          <p class="cc-klein">{{ t("describe.busy", { seconds }) }}</p>
        </div>

        <!-- 3b. Earlier descriptions of this object, to choose from again (free). -->
        <cdx-accordion v-if="history.length" v-model="openHistory" class="cc-beschrijving-blok">
          <template #title>{{ t("describe.history", { n: history.length }) }}</template>
          <template #description>{{ t("describe.history_short") }}</template>
          <!-- One version at a time: Previous / Next, "2 of 5" and dots (VersionCarousel.vue). -->
          <version-carousel :items="history" item-key="versie" :label="t('describe.history_short')">
            <template #default="{ item: entry }">
              <div
                class="cc-geschiedenis-tekstblok"
                :class="{ open: expanded[entry.versie] }"
                role="button"
                tabindex="0"
                :aria-expanded="expanded[entry.versie] ? 'true' : 'false'"
                :title="expanded[entry.versie] ? '' : fullText(entry)"
                @click="expanded[entry.versie] = !expanded[entry.versie]"
                @keydown.enter.space.prevent="expanded[entry.versie] = !expanded[entry.versie]"
              >
                <strong>{{ language === "en" ? entry.onderwerp_en || entry.onderwerp : entry.onderwerp || entry.onderwerp_en }}</strong>
                <span class="cc-klein cc-geschiedenis-beschrijving">{{ language === "en" ? entry.beschrijving_en || entry.beschrijving : entry.beschrijving || entry.beschrijving_en }}</span>
                <span v-if="entry.tekst_in_beeld" class="cc-klein cc-geschiedenis-beschrijving">{{ t("describe.field_tekst_in_beeld") }}: {{ entry.tekst_in_beeld }}</span>
                <span v-if="entry.tekst_rond_beeld" class="cc-klein cc-geschiedenis-beschrijving">{{ t("describe.field_tekst_rond_beeld") }}: {{ entry.tekst_rond_beeld }}</span>
                <span class="cc-klein cc-geschiedenis-meta">{{ historyMeta(entry) }}</span>
                <span class="cc-link cc-klein cc-geschiedenis-meer">{{ expanded[entry.versie] ? t("describe.history_less") : t("describe.history_more") }}</span>
              </div>
            </template>
            <template #actions="{ item: entry }">
              <cdx-button action="progressive" size="small" :disabled="busy" @click="restoreDescription(entry)">{{ t("describe.history_use") }}</cdx-button>
              <cdx-button action="destructive" weight="quiet" size="small" :disabled="busy" :aria-label="t('describe.history_delete')" :title="t('describe.history_delete')" @click="deleteVersion(entry)">
                <cdx-icon :icon="cdxIconTrash" size="small" />
              </cdx-button>
            </template>
          </version-carousel>
        </cdx-accordion>

        <!-- Suggestions for depicts: the next step after a description. -->
        <section class="cc-blok" :class="{ 'cc-menu-open': lookupItems.length && ownTerm.trim().length >= 2 }">
          <h3 class="cc-blok-kop">
            {{ t("describe.suggestions") }}
            (<a href="https://www.wikidata.org/wiki/Property:P180" target="_blank" rel="noopener">P180</a>)
          </h3>
          <p v-if="description?.wikidata_suggesties?.length" class="cc-klein">{{ t("describe.suggestions_help") }}</p>
          <!-- Search Wikidata yourself (free, only reading). -->
          <!-- Autosuggest while typing (Codex Lookup); choosing an item adds it to 'beeldt af'.
               Enter or Zoeken shows all results as a list below. -->
          <form class="cc-zoek cc-wikidata-zoek" @submit.prevent="searchWikidata(ownTerm)">
            <cdx-lookup
              v-model:selected="lookupChoice"
              v-model:input-value="ownTerm"
              :menu-items="lookupItems"
              :menu-config="{ visibleItemLimit: 8 }"
              :start-icon="cdxIconSearch"
              :placeholder="t('describe.search_placeholder')"
              :aria-label="t('describe.search_label')"
              @input="onLookupInput"
              @update:selected="onLookupSelect"
            >
              <template #no-results><template v-if="lookupDone">{{ t("describe.search_none", { term: ownTerm }) }}</template><template v-else>{{ t("describe.search_busy") }}</template></template>
            </cdx-lookup>
            <cdx-button type="submit" action="progressive" :disabled="!ownTerm.trim()">{{ t("describe.search_button") }}</cdx-button>
          </form>
          <div v-if="description?.wikidata_suggesties?.length" class="cc-knoppen">
            <cdx-button action="progressive" v-for="term in description.wikidata_suggesties" :key="term" size="small" @click="searchWikidata(term)">
              <cdx-icon :icon="cdxIconSearch" /> {{ term }}
            </cdx-button>
          </div>
          <p v-if="searched && !hits.length" class="cc-klein">{{ t("describe.search_none", { term: searched }) }}</p>
          <ul v-if="hits.length" class="cc-treffers">
            <li v-for="hit in hits" :key="hit.q">
              <cdx-button size="small" weight="quiet" action="progressive" @click="addDepicts(hit)">+ {{ hit.label }}</cdx-button>
              <small><a :href="`https://www.wikidata.org/wiki/${hit.q}`" target="_blank" rel="noopener">{{ hit.q }}</a> · {{ hit.beschrijving }}</small>
            </li>
          </ul>
        </section>

        <!-- 3c. Secondary: which model, why, what this answer cost, and how far to trust it. -->
        <cdx-accordion v-if="plan || description" class="cc-beschrijving-blok">
          <template #title>{{ t("describe.model_block") }}</template>
          <template #description>{{ (description || plan).model }}</template>
          <p class="cc-klein">
            <template v-for="(part, i) in textParts(modelReason, reasonLinks)" :key="i">
              <a v-if="part.link" :href="part.link.href" target="_blank" rel="noopener">{{ part.link.label }}</a>
              <template v-else>{{ part.text }}</template>
            </template>
            <template v-if="description?.alleen_naar"><br />{{ t("describe.group_used", { members: description.alleen_naar }) }}</template>
            <template v-if="description?.aanwijzing"><br />{{ t("describe.hint_used", { hint: description.aanwijzing }) }}</template>
            <template v-if="description && description.kosten_usd != null">
              <br />{{ t("describe.paid", { amount: money(description.kosten_usd, language) }) }}
              <template v-if="description.tokens?.invoer != null"> · {{ t("describe.tokens", { input: description.tokens.invoer, output: description.tokens.uitvoer }) }}</template>
            </template>
          </p>
          <p class="cc-klein cc-waarschuwing">{{ t("describe.caution") }}</p>
        </cdx-accordion>
      </cdx-tab>

      <cdx-tab name="commons" :label="t('concept.tab')">
        <concept-editor ref="editor" :mid="file.mid" :n="n" :object-id="object.id" @texts-changed="emit('changed', $event)" />
      </cdx-tab>
    </cdx-tabs>
    <cdx-message v-if="error" type="error" :inline="true">{{ error }}</cdx-message>
  </cdx-dialog>
</template>

<script setup>
import { computed, inject, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { CdxAccordion, CdxButton, CdxDialog, CdxField, CdxIcon, CdxInfoChip, CdxLookup, CdxMessage, CdxProgressBar, CdxTab, CdxTabs, CdxTextArea, CdxTextInput, CdxToggleButtonGroup, CdxToggleSwitch } from "@wikimedia/codex";
import { cdxIconClose, cdxIconDownload, cdxIconEdit, cdxIconLinkExternal, cdxIconNext, cdxIconPrevious, cdxIconSearch, cdxIconTrash } from "@wikimedia/codex-icons";
import { API, del, errorText, get, objectPath, patch, post, put } from "../api.js";
import { askConfirm, textParts } from "../confirm.js";
import { money, useT } from "../i18n.js";
import VersionCarousel from "./VersionCarousel.vue";
import DetailSlider from "./DetailSlider.vue";
import BusyNote from "./BusyNote.vue";
import ZoomImage from "./ZoomImage.vue";
import SavedLabel from "./SavedLabel.vue";
import { forgetPlacement, makeMovable } from "../movable.js";
import { fileName, objectName, savedLabel } from "../state.js";
import { searchItems, wikidataSearcher } from "../wikidata.js";
import { fitToText } from "../autosize.js";
import AiBadge from "./AiBadge.vue";
import ConceptEditor from "./ConceptEditor.vue";
import CutoutPreview from "./CutoutPreview.vue";
import RetentionInfo from "./RetentionInfo.vue";

const props = defineProps({
  open: { type: Boolean, default: false },
  file: { type: Object, required: true },
  n: { type: Number, required: true },
  object: { type: Object, required: true },
  // Where this object is in the list: {index (1-based), total}.
  position: { type: Object, default: () => ({ index: 1, total: 1 }) },
  // The name as the list shows it ("boom 2"), for the title only.
  listName: { type: String, default: "" },
});
const emit = defineEmits(["update:open", "changed", "trashed", "refine", "step"]);

// ← and → go to the previous and next object, except while typing or on a slider.
function onStepKey(event) {
  if (!props.open || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
  if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
  const target = event.target;
  if (target?.closest?.("input, textarea, select, [contenteditable='true'], [role='slider'], [role='tab'], [role='tablist']")) return;
  event.preventDefault();
  step(event.key === "ArrowLeft" ? -1 : 1);
}
onMounted(() => window.addEventListener("keydown", onStepKey));
const t = useT();
const language = inject("language", "nl");
const config = inject("config");
const tab = ref("uitsnede");
const caption = ref(props.object.bijschrift?.tekst || "");
const savedInfo = computed(() => savedLabel(props.object, t, language));
const plan = ref(null);
const busy = ref(false);
const seconds = ref(0);
let ticker = null;
const error = ref("");
// The hint for the next "Ask again" (sent once, then cleared).
const hint = ref("");
// Folded away until wanted: the AI modifiers and the earlier descriptions.
const openModifiers = ref(false);
const openHistory = ref(false);

// Where the preview sits: beside the slider while the AI modifiers are open.
// It moves as soon as they start to open or close (the fold itself is
// animated by accordion-motion.js), and glides there: a copy flies from the
// old place to the new one, above everything, so the folding content does not
// clip it (FLIP: measure before and after, animate the difference).
const previewInModifiers = ref(false);
watch(openModifiers, (open) => {
  previewInModifiers.value = open;
});
function visiblePreview() {
  return [...document.querySelectorAll(".cc-vergroter .cc-ai-voorbeeld")].find((el) => el.offsetParent);
}
let previewBefore = null;
watch(previewInModifiers, () => (previewBefore = visiblePreview()?.getBoundingClientRect() || null), { flush: "pre" });
watch(previewInModifiers, async () => {
  await nextTick();
  const el = visiblePreview();
  if (!el || !previewBefore || window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
  // Measured after the accordion has started to open, so the target is known.
  await new Promise((resolve) => requestAnimationFrame(resolve));
  const after = el.getBoundingClientRect();
  const flyer = el.cloneNode(true);
  Object.assign(flyer.style, {
    position: "fixed", left: `${previewBefore.left}px`, top: `${previewBefore.top}px`, width: `${after.width}px`,
    margin: "0", zIndex: "1000", pointerEvents: "none",
  });
  document.body.appendChild(flyer);
  el.style.visibility = "hidden";
  const move = flyer.animate(
    [{ transform: "translate(0, 0)" }, { transform: `translate(${after.left - previewBefore.left}px, ${after.top - previewBefore.top}px)` }],
    { duration: 600, easing: "cubic-bezier(0.65, 0, 0.35, 1)" } // speeds up, then slows down
  );
  move.onfinish = move.oncancel = () => {
    el.style.visibility = "";
    flyer.remove();
  };
});
// A group (7.4): its members by the names of the list, e.g. "cardboard box and Boy in white sailor suit with box".
const groupMemberNames = computed(() => (props.object.groep?.leden || []).map((m) => objectName(m, language, t)));
// The members' earlier descriptions that go along with the question (in English, as sent).
const groupContext = computed(() =>
  (props.object.groep?.leden || [])
    .filter((m) => m.beschrijving?.beschrijving_en)
    .map((m) => ({ name: objectName(m, language, t), text: m.beschrijving.beschrijving_en, inText: m.beschrijving.tekst_in_beeld, around: m.beschrijving.tekst_rond_beeld }))
);
// The text around the members, which are shown as pills in between.
// With space around the cut-out, the sentence lets the AI use the surroundings as context (as the server does).
const groupFocus = computed(() =>
  [...t(margin.value > 0 ? "describe.group_focus_context" : "describe.group_focus", { names: "@@names@@" }).split("@@names@@"), ""].slice(0, 2)
);
// "Only these objects": switched off, the group is described as a plain cut-out.
const groupOnly = ref(true);
const groupNames = computed(() => {
  const names = groupMemberNames.value;
  if (!names.length) return "";
  return names.length === 1 ? names[0] : `${names.slice(0, -1).join(", ")} ${t("describe.and")} ${names[names.length - 1]}`;
});
// How much of the surroundings the AI sees, as a share of the box on every
// side (0-1): what the last description used, else 25 %.
const DEFAULT_MARGIN = 0.25;
const margin = ref(props.object.beschrijving?.marge ?? DEFAULT_MARGIN);
// How long the description is (the same stops as for the whole image): what the last answer used.
const OBJECT_DESCRIPTION_LEVELS = ["kort", "normaal", "caption", "uitgebreid"];
const descLevel = ref(props.object.beschrijving?.beschrijvingsniveau || "normaal");
// What the next question will use besides the defaults, in a few words
// (shown beside the button and on the folded AI modifiers).
const modifiersSummary = computed(() => {
  const parts = [];
  if (props.object.groep && !groupOnly.value) parts.push(t("describe.history_group_off"));
  if (descLevel.value !== "normaal") parts.push(t("descdetail.used", { level: t(`objdetail.${descLevel.value}`) }));
  if (Math.round(margin.value * 100) !== Math.round(DEFAULT_MARGIN * 100)) parts.push(t("describe.history_margin", { pct: Math.round(margin.value * 100) }));
  if (hint.value.trim()) parts.push(t("describe.history_hint", { hint: hint.value.trim() }));
  return parts.join(" · ");
});
// The preview follows the slider a moment after it stops moving.
const shownMargin = ref(margin.value);
let marginTimer = null;
watch(margin, (value) => {
  clearTimeout(marginTimer);
  marginTimer = setTimeout(() => (shownMargin.value = value), 250);
});
const hits = ref([]);
const editor = ref(null);

// Move by the title bar, resize at the edges; double-click the title bar to
// centre it again. Codex renders the dialog elsewhere in the page (teleport).
const PLACEMENT_KEY = "cc-vergroter-plaats";
let undoMovable = null;

function enableMoving() {
  undoMovable?.();
  undoMovable = null;
  const dialog = document.querySelector(".cc-vergroter");
  const header = dialog?.querySelector(".cdx-dialog__header");
  if (!dialog || !header) return;
  undoMovable = makeMovable(dialog, {
    handle: header,
    storageKey: PLACEMENT_KEY,
    labels: { move: t("magnifier.move"), resize: t("magnifier.resize") },
    min: { width: 360, height: 240 },
  });
  header.ondblclick = (event) => {
    if (event.target.closest("button")) return;
    forgetPlacement(PLACEMENT_KEY);
    dialog.removeAttribute("style");
  };
}

watch(
  () => props.open,
  async (open) => {
    if (!open) {
      saveCaptionIfChanged();
      undoMovable?.();
      undoMovable = null;
      return;
    }
    await nextTick();
    enableMoving();
  },
  { immediate: true }
);
// Closing: no timer, interval or search keeps running.
onBeforeUnmount(() => {
  window.removeEventListener("keydown", onStepKey);
  undoMovable?.();
  clearTimeout(marginTimer);
  clearInterval(ticker);
  lookupSearcher.stop();
});

const base = computed(() => objectPath(props.file.mid, props.n, props.object.id));
const name = computed(() => objectName(props.object, language, t));
const subtitle = computed(() => `${t(`source.${props.object.bron}`)} · ${t(`status.${props.object.status}`)}`);
const description = computed(() => props.object.beschrijving || null);
// Whether the user changed this AI text (NL or EN) by hand.
function aiEdited(field) {
  const original = description.value?.ai_origineel || {};
  return field in original || `${field}_en` in original;
}

// Kind and certainty come from a fixed Dutch list (the model's answer schema);
// shown in the interface language, or as given when not in the list.
function fixedValue(group, value) {
  const text = t(`${group}.${value}`);
  return text === `${group}.${value}` ? value : text;
}
// Why this model, in plain words. Descriptions stored before the reason had a
// code fall back to the current choice for the file (the same rules).
const modelReason = computed(() => {
  const d = description.value;
  const code = d ? d.model_reden_code || plan.value?.reden_code : plan.value?.reden_code;
  if (!code) return d?.model_reden || plan.value?.reden || "";
  const labels = (d?.model_reden_labels || plan.value?.labels || []).map((label) => t(`rights.${label}`)).join(", ");
  return t(`describe.reason_${code}`, { labels });
});
// "Contributor" links to Meta's explanation of that mode (cheaper; Meta may train on the input).
const reasonLinks = {
  contributor: { href: "https://dev.meta.ai/docs/pricing-rate-limits#contributor-mode", label: t("describe.contributor_link") },
};
// The cost on the buttons: an estimate in live mode, free with the dummy.
const costLabel = computed(() => (plan.value?.betaald ? `± ${money(plan.value.kosten_schatting_usd, language)}` : t("describe.free_short")));
// What the image description would see with the chosen margin (free; nothing goes to the model).
const modelInputUrl = computed(() => `${base.value}/beschrijving/invoer.jpg?marge=${shownMargin.value}`);
// The same, large (up to 3000 px), for the lightbox: to read and check the text in the image.
const largeInputUrl = computed(() => `${modelInputUrl.value}&max=3000`);
// The texts the AI read, beside the large image in the lightbox, to compare.
const readTexts = computed(() =>
  description.value
    ? [
        ...READ_TEXTS.map((key) => ({
          key,
          label: t(`describe.field_${key}`),
          text: description.value[key],
          ai: true,
          model: description.value.model,
          edited: key in (description.value.ai_origineel || {}),
        })),
      ]
    : []
);
// View on the Cut-out tab: the shape (PNG, transparent) or the rectangle (JPG).
// Only a view; what goes to Commons is the format in the Commons concept.
const views = [
  { value: "png", label: "PNG" },
  { value: "jpg", label: "JPG" },
];
const view = ref(props.object.masker ? "png" : "jpg");
// "loading" until the browser has the cut-out; again after switching between PNG and JPG.
const imageState = ref("loading");
const imageUrl = computed(() => (props.object.masker && view.value === "png" ? `${base.value}/uitsnede.png` : `${base.value}/uitsnede.jpg?w=1200`));
watch(imageUrl, () => {
  imageState.value = "loading";
});

watch(
  () => props.object.id,
  () => {
    caption.value = props.object.bijschrift?.tekst || "";
    view.value = props.object.masker ? "png" : "jpg";
    removedCaption.value = "";
    hint.value = "";
    margin.value = props.object.beschrijving?.marge ?? DEFAULT_MARGIN;
    descLevel.value = props.object.beschrijving?.beschrijvingsniveau || "normaal";
    shownMargin.value = margin.value;
    loadHistory();
    cancelEditing();
    undoTexts.value = null;
    hits.value = [];
    // Nothing of the previous object's search or errors stays in view.
    lookupSearcher.stop();
    fullSearch += 1;
    searched.value = "";
    ownTerm.value = "";
    lookupItems.value = [];
    error.value = "";
    loadPlan();
  }
);

async function loadPlan() {
  try {
    plan.value = await get(`${base.value}/beschrijving`);
  } catch (e) {
    error.value = errorText(t, e);
  }
}
loadPlan();

async function describe(again) {
  // Asking again always costs money; a first question may still come from the
  // cache (free), but the estimate is asked to confirm all the same.
  const paid = again || !description.value;
  if (paid && config.betaald && plan.value?.betaald && !(await askConfirm(`${t("confirm.action_describe", { name: name.value })}\n\n${t("describe.confirm", { amount: money(plan.value.kosten_schatting_usd, language) })}`, { title: t("confirm.cost_title") }))) return;
  busy.value = true;
  seconds.value = 0;
  ticker = setInterval(() => seconds.value++, 1000);
  error.value = "";
  try {
    const body = { opnieuw: again, marge: margin.value, beschrijvingsniveau: descLevel.value };
    if (props.object.groep && !groupOnly.value) body.alleen_groep = false;
    if (hint.value.trim()) body.aanwijzing = hint.value.trim();
    const result = await post(`${base.value}/beschrijving`, body);
    emit("changed", result.object);
    hint.value = "";
    cancelEditing();
    undoTexts.value = null;
    editor.value?.reload();
    loadHistory();
  } catch (e) {
    error.value = errorText(t, e);
  } finally {
    busy.value = false;
    clearInterval(ticker);
  }
}

// Earlier descriptions (kept history plus answers still in the cache), newest first.
const history = ref([]);

async function loadHistory() {
  try {
    history.value = (await get(`${base.value}/beschrijving/geschiedenis`)).geschiedenis;
  } catch {
    history.value = [];
  }
}
loadHistory();

// Earlier versions: unfolded ones (by versie), and the whole text for the hover popup.
const expanded = reactive({});
function fullText(entry) {
  return [
    [entry.onderwerp, entry.beschrijving].filter(Boolean).join(" — "),
    [entry.onderwerp_en, entry.beschrijving_en].filter(Boolean).join(" — "),
    entry.tekst_in_beeld && `${t("describe.field_tekst_in_beeld")}: ${entry.tekst_in_beeld}`,
    entry.tekst_rond_beeld && `${t("describe.field_tekst_rond_beeld")}: ${entry.tekst_rond_beeld}`,
  ].filter(Boolean).join("\n\n");
}

// When and how a version was made: by hand (the time of the edit) or by the AI (time, model, question).
function historyMeta(entry) {
  const time = (value) => (value ? new Date(value).toLocaleString(language, { dateStyle: "short", timeStyle: "short" }) : "");
  if (entry.bewerkt_op) return [t("describe.history_by_hand", { when: time(entry.bewerkt_op) }), entry.model].filter(Boolean).join(" · ");
  const when = time(entry.tijdstempel);
  const parts = [when, entry.model];
  if (entry.aanwijzing) parts.push(t("describe.history_hint", { hint: entry.aanwijzing }));
  parts.push(t("describe.history_margin", { pct: Math.round((entry.marge ?? DEFAULT_MARGIN) * 100) }));
  if (entry.bewerkt) parts.push(t("describe.edited"));
  return parts.filter(Boolean).join(" · ");
}

// Delete one earlier version (after a confirmation); the list follows the server.
async function deleteVersion(entry) {
  const ok = await askConfirm(t("describe.history_delete_confirm"), { title: t("describe.history_delete"), go: t("describe.history_delete"), destructive: true });
  if (!ok) return;
  error.value = "";
  try {
    history.value = (await del(`${base.value}/beschrijving/geschiedenis/${encodeURIComponent(entry.versie)}`)).geschiedenis;
  } catch (e) {
    error.value = errorText(t, e);
  }
}

// Make an earlier description current again; the current one goes into the history.
async function restoreDescription(entry) {
  error.value = "";
  try {
    const changed = await put(`${base.value}/beschrijving`, { versie: entry.versie });
    emit("changed", changed);
    cancelEditing();
    undoTexts.value = null;
    margin.value = changed.beschrijving?.marge ?? DEFAULT_MARGIN;
    editor.value?.reload();
    loadHistory();
  } catch (e) {
    error.value = errorText(t, e);
  }
}

// Forget the description; the answer stays in the cache, so asking again is free.
async function removeDescription() {
  if (!(await askConfirm(t("describe.remove_confirm"), { go: t("describe.remove"), destructive: true }))) return;
  try {
    emit("changed", await del(`${base.value}/beschrijving`));
    cancelEditing();
    undoTexts.value = null;
    editor.value?.reload();
    loadPlan();
    loadHistory();
  } catch (e) {
    error.value = errorText(t, e);
  }
}

// Editing the AI texts by hand, one field (or NL/EN pair) at a time with its own
// pencil. The server keeps the original AI text, for "Terug naar de AI-tekst";
// "Ongedaan maken" puts back what was there before the last change.
const READ_TEXTS = ["tekst_in_beeld", "tekst_rond_beeld"];
const EDITABLE = ["onderwerp", "onderwerp_en", "bedrijf_of_naam", "beschrijving", "beschrijving_en", ...READ_TEXTS];
const TEXT_GROUPS = [
  { key: "onderwerp", label: "describe.subject", fields: ["onderwerp", "onderwerp_en"], ai: true, always: true },
  { key: "naam", label: "describe.name", fields: ["bedrijf_of_naam"] },
  { key: "beschrijving", label: "describe.description", fields: ["beschrijving", "beschrijving_en"], ai: true, always: true, long: true },
  { key: "tekst_in_beeld", label: "describe.field_tekst_in_beeld", fields: ["tekst_in_beeld"], read: true, long: true },
  { key: "tekst_rond_beeld", label: "describe.field_tekst_rond_beeld", fields: ["tekst_rond_beeld"], read: true, long: true },
];
const editingGroup = ref(null);
const fieldDraft = ref({});
const undoTexts = ref(null);

function currentTexts() {
  return Object.fromEntries(EDITABLE.map((field) => [field, description.value?.[field] || ""]));
}

const fieldChanged = computed(() => Object.entries(fieldDraft.value).some(([field, value]) => value.trim() !== (description.value?.[field] || "")));

const editBox = ref(null);
async function startEditing(group) {
  editingGroup.value = group.key;
  fieldDraft.value = Object.fromEntries(group.fields.map((field) => [field, description.value?.[field] || ""]));
  // As high as the text itself right away (autosize only reacts once you type).
  await nextTick();
  const box = Array.isArray(editBox.value) ? editBox.value[0] : editBox.value;
  box?.querySelectorAll("textarea").forEach(fitToText);
  box?.querySelector("textarea, input")?.focus();
}

function cancelEditing() {
  editingGroup.value = null;
  fieldDraft.value = {};
}

function saveEditing() {
  if (fieldChanged.value) saveTexts({ ...fieldDraft.value });
}

async function saveTexts(texts, { undoable = true } = {}) {
  const before = currentTexts();
  try {
    emit("changed", await patch(`${base.value}/beschrijving`, texts));
    cancelEditing();
    loadHistory(); // the version before this edit is now in Eerdere beschrijvingen
    undoTexts.value = undoable ? before : null;
    editor.value?.reload();
  } catch (e) {
    error.value = errorText(t, e);
  }
}

function backToAi() {
  saveTexts({ ...currentTexts(), ...description.value.ai_origineel });
}

function undoEdit() {
  saveTexts(undoTexts.value, { undoable: false });
}

// Empty the caption and remove it from the object at once (no Opslaan needed);
// what was there can be put back with "Ongedaan maken".
const removedCaption = ref("");

async function removeCaption() {
  const previous = (props.object.bijschrift?.tekst || caption.value).trim();
  caption.value = "";
  await saveCaption();
  removedCaption.value = previous;
}

async function undoRemoveCaption() {
  caption.value = removedCaption.value;
  removedCaption.value = "";
  await saveCaption();
}

// A caption typed but not saved is saved anyway when you leave the tab
// "Uitsnede", go to another object or close the magnifier: "Wat staat hierop?"
// then sees it at once.
const captionDirty = computed(() => caption.value.trim() !== (props.object.bijschrift?.tekst || "").trim());
async function saveCaptionIfChanged() {
  if (captionDirty.value) await saveCaption();
}
watch(tab, (now, before) => {
  if (before === "uitsnede" && now !== "uitsnede") saveCaptionIfChanged();
});
async function step(direction) {
  await saveCaptionIfChanged();
  emit("step", direction);
}

async function saveCaption() {
  try {
    const text = caption.value.trim();
    const result = await patch(base.value, { bijschrift: text ? { tekst: text } : null });
    emit("changed", result);
  } catch (e) {
    error.value = errorText(t, e);
  }
}

const ownTerm = ref("");
const searched = ref("");
// Autosuggest: Wikidata items as you type, after 2 letters and a short pause.
const lookupItems = ref([]);
const lookupChoice = ref(null);
const lookupDone = ref(false); // "nothing found" only after an answer, not while waiting
const lookupSearcher = wikidataSearcher(language);
function onLookupInput(value) {
  lookupSearcher.search(value, (items, done) => {
    if (items) lookupItems.value = items;
    lookupDone.value = done;
  });
}
let fullSearch = 0;
async function onLookupSelect(q) {
  const item = lookupItems.value.find((entry) => entry.value === q);
  if (!item) return;
  await addDepicts(item.hit);
  lookupChoice.value = null;
}
async function searchWikidata(term) {
  term = (term || "").trim();
  if (!term) return;
  const mine = ++fullSearch;
  try {
    const found = await searchItems(term, language);
    if (mine !== fullSearch) return; // a newer search (or another object) came first
    hits.value = found;
    searched.value = term;
  } catch (e) {
    error.value = errorText(t, e);
  }
}

async function addDepicts(hit) {
  await editor.value?.addDepicts({ q: hit.q, label: hit.label });
  tab.value = "commons";
}

// Download saves the file (named after the Commons concept); view opens it in a new tab.
function download(kind) {
  window.location.href = `${base.value}/uitsnede.${kind}?download=1`;
}

function viewFull(kind) {
  window.open(`${base.value}/uitsnede.${kind}`, "_blank", "noopener");
}

// -- AI-completed version (Muse Image, 7.7) --------------------------------------------------

const completing = ref(false);
// The prompt of the AI-completed version, exactly as it went to the model (in English),
// with the subject shown as a pill wherever it occurs. Older versions did not keep it:
// then a summary of it.
const completionPrompt = computed(() => {
  const note = props.object.aangevuld;
  if (!note) return [];
  const subject = note.onderwerp || "";
  const text = note.prompt || t("completion.prompt", { subject });
  if (!subject) return [{ text }];
  return text.split(subject).flatMap((piece, i) => (i ? [{ text: subject, pill: true }, { text: piece }] : [{ text: piece }])).filter((part) => part.text);
});
// The overlay with what the AI filled in, switched on and off (remembered while the magnifier is open).
const showFilled = ref(false);
// Another object without an AI-completed version: back to the cut-out tab.
watch(
  () => props.object.aangevuld,
  (note) => {
    if (!note && !completionHistory.value.length && tab.value === "aangevuld") tab.value = "uitsnede";
    editingPrompt.value = false;
  }
);
const completionError = ref("");
const completionCost = computed(() => (config.betaald ? `(${money(config.aanvulling_usd, language)})` : t("panel.free")));

// Paid in live mode: first a confirmation with the amount and what it is (invented, not a source).
async function complete() {
  completionError.value = "";
  const again = Boolean(props.object.aangevuld);
  if (config.betaald) {
    const text = t("completion.confirm", { amount: money(config.aanvulling_usd, language) });
    if (!(await askConfirm(text, { title: t("confirm.cost_title") }))) return;
  }
  completing.value = true;
  try {
    // Your own prompt, when you changed it with the pencil.
    const own = editingPrompt.value && promptDraft.value.trim() ? { prompt: promptDraft.value.trim() } : {};
    const result = await post(`${base.value}/aanvulling`, { opnieuw: again, ...own });
    editingPrompt.value = false;
    emit("changed", result.object);
    // Show the result in its own tab, once it is there.
    await nextTick();
    tab.value = "aangevuld";
  } catch (failure) {
    completionError.value = errorText(t, failure);
  } finally {
    completing.value = false;
  }
}

async function forgetCompletion() {
  if (!(await askConfirm(t("completion.remove_confirm", { days: config.bewaren?.uitsneden ?? 30 }), { title: t("completion.remove"), go: t("completion.remove"), destructive: true }))) return;
  try {
    emit("changed", (await del(`${base.value}/aanvulling`)).object);
  } catch (failure) {
    completionError.value = errorText(t, failure);
  }
}

// The prompt for the next "Complete again": start from the current one; the app's own is one click away.
const editingPrompt = ref(false);
const promptDraft = ref("");
function startPrompt() {
  promptDraft.value = props.object.aangevuld?.prompt || "";
  editingPrompt.value = true;
}
async function resetPrompt() {
  try {
    promptDraft.value = (await get(`${base.value}/aanvulling`)).standaard_prompt || promptDraft.value;
  } catch (failure) {
    completionError.value = errorText(t, failure);
  }
}
const completionHistory = computed(() => props.object.aangevuld_geschiedenis || []);
async function useCompletion(entry) {
  completionError.value = "";
  try {
    emit("changed", (await put(`${base.value}/aanvulling`, { sleutel: entry.sleutel })).object);
  } catch (failure) {
    completionError.value = errorText(t, failure);
  }
}
async function deleteCompletion(entry) {
  if (!(await askConfirm(t("completion.history_delete_confirm"), { title: t("describe.history_delete"), go: t("describe.history_delete"), destructive: true }))) return;
  try {
    emit("changed", (await del(`${base.value}/aanvulling/geschiedenis/${encodeURIComponent(entry.sleutel)}`)).object);
  } catch (failure) {
    completionError.value = errorText(t, failure);
  }
}
const formatTime = (stamp) => (stamp ? new Date(stamp).toLocaleString(language === "en" ? "en-GB" : "nl-NL", { dateStyle: "medium", timeStyle: "short" }) : "");

function downloadCompletion() {
  window.location.href = `${base.value}/aangevuld.png?download=1`;
}

function viewCompletion() {
  window.open(`${base.value}/aangevuld.png`, "_blank", "noopener");
}
</script>

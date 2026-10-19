/* Data is rendered as text, never injected HTML. All local links are allowlisted. */
'use strict';
const $ = (selector) => document.querySelector(selector);
const playbackURLs = new Set();
const pendingLoads = new Set();
function node(tag, text, className) {
  const e = document.createElement(tag);
  if (text !== undefined) e.textContent = text;
  if (className) e.className = className;
  return e;
}
function localURL(path) {
  const u = new URL(path, location.href);
  const base = new URL('.', location.href);
  if (u.origin !== base.origin || !u.pathname.startsWith(base.pathname)) throw Error('Unsafe artifact link');
  return u.href;
}
function link(label, href, external = false) {
  const a = node('a', label);
  if (external) {
    const u = new URL(href);
    if (u.protocol !== 'https:') throw Error('Unsafe reference');
    a.href = u.href; a.target = '_blank'; a.rel = 'noopener noreferrer';
  } else a.href = localURL(href);
  return a;
}
function shortVersion(b) { return b ? b.environment.environment_relative_to_project.split('/').at(-1) : 'No feasible cycle'; }
function count(b) { return b ? `${b.complete_cycles} / ${b.admissible_manipulation_trials}` : 'Not eligible'; }
function details(title, children) {
  const d = node('details'); d.append(node('summary', title), ...children); return d;
}
function card(c) {
  const article = node('article', undefined, 'card'); article.id = `design-${c.id}`;
  if (c.image) {
    const figure = node('figure'); const img = node('img');
    img.src = localURL(c.image); img.alt = `${c.id}: ${c.image_caption}`; img.loading = 'lazy';
    figure.append(img, node('figcaption', c.image_caption)); article.append(figure);
  } else {
    const placeholder = node('div', undefined, 'placeholder');
    placeholder.append(node('strong', `${c.id[0]} / ${c.id[1]}`), node('span', 'Representative render pending'));
    article.append(placeholder);
  }
  const content = node('div', undefined, 'card-content');
  const currentPass = c.current ? c.current.passed : Boolean(c.benchmark);
  content.append(node('span', c.current ? `${c.current.version} · ${currentPass ? 'NOMINAL CYCLE PASSED' : 'FEASIBILITY FAILED'}` : (currentPass ? 'FEASIBILITY + RANDOMIZED TRIALS' : 'FAILED FEASIBILITY · PRESERVED'), `badge${currentPass ? '' : ' failed'}`),
    node('h3', `${c.id[0]} / ${c.id[1]} · ${c.architecture}`), node('p', c.tool, 'tool-name'),
    node('p', c.architecture_description), node('p', c.tool_description, 'muted'));
  const refs = node('div', undefined, 'links');
  refs.append(link('Mechanism reference ↗', c.architecture_reference, true), link('Tool reference ↗', c.tool_reference, true)); content.append(refs);
  if (c.current) {
    content.append(node('p', `Current ${c.current.version}: ${c.current.passed ? 'complete nominal cycle' : 'failed nominal attempt'}${c.current.cycle_time_s != null ? ` · ${c.current.cycle_time_s.toFixed(2)} s` : ''}. ${c.current.declared_outcome_verified ? 'Fresh reload reproduces this outcome.' : 'Outcome reproduction is unverified.'}`));
    if (c.current.error) content.append(node('p', String(c.current.error), 'version-warning'));
    content.append(link('Current feasibility result', c.current.result_link));
  }
  if (c.current_benchmark) {
    const b = c.current_benchmark;
    const currentStats = node('div', undefined, 'current-cohort');
    currentStats.append(node('strong', `Current ${c.current.version} · completed randomized cohort`),
      node('p', `${b.complete_cycles} / ${b.planned} planned starts completed the cycle. ${b.fixture_failures} fixture failures before manipulation.`),
      node('p', `${b.complete_cycles} / ${b.admissible_manipulation_trials} valid manipulation trials passed; 95% Wilson interval ${b.wilson_95_interval ? b.wilson_95_interval.map(v=>(100*v).toFixed(1)+'%').join('–') : 'insufficient valid trials'}.`),
      node('p', `Mean successful cycle ${b.mean_successful_cycle_s == null ? 'unavailable' : b.mean_successful_cycle_s.toFixed(2)+' s'}. No physical-hardware reliability claim.`, 'muted'),
      link('Current cohort evidence', b.summary_source));
    content.append(currentStats);
  } else if (c.current?.passed) {
    content.append(node('p', 'Current-version randomized cohort not yet included. Historical results below are not a substitute.', 'version-warning'));
  }
  const numbers = node('div', undefined, 'numbers');
  numbers.append(node('strong', count(c.benchmark)), node('p', `Historical complete cycles · ${shortVersion(c.benchmark)}`, 'muted'));
  if (c.neighbors) numbers.append(node('p', `${c.neighbors.clearance_passes} / ${c.neighbors.cases} neighbor-clearance passes · ${c.neighbors.cases_with_robot_neighbor_contact} cases with robot contact`, 'muted'));
  content.append(numbers);
  const latest = c.versions.at(-1);
  if (c.benchmark && latest.version !== shortVersion(c.benchmark)) content.append(node('p', `Newer ${latest.version} is preserved below. The statistics above do NOT apply to it.`, 'version-warning'));
  const clips = c.media.map(m => {
    const div = node('div', undefined, 'clip');
    const video = node('video'); video.controls = true; video.preload = 'none'; video.playsInline = true;
    video.setAttribute('aria-label', m.label);
    const load = node('button', 'Load playable clip'); load.type = 'button'; load.className = 'load-clip';
    const loading = node('p', 'Loads this clip into browser memory for seeking. Nothing autoplays.', 'muted');
    loading.setAttribute('aria-live', 'polite');
    load.addEventListener('click', async () => {
      const controller = new AbortController(); pendingLoads.add(controller);
      load.disabled = true; loading.textContent = 'Downloading clip through the SSH tunnel…';
      try {
        // The preserved Python artifact server has no HTTP byte-range support.
        // A user-requested complete Blob enables reliable local seeking without
        // replacing that server (a child of the live desktop supervisor).
        const response = await fetch(localURL(m.url), {signal:controller.signal});
        if (!response.ok) throw Error(`HTTP ${response.status}`);
        const blob = await response.blob();
        if (!video.isConnected) return;
        const url = URL.createObjectURL(blob); playbackURLs.add(url);
        video.src = url; video.preload = 'metadata'; video.load();
        video.dataset.loaded = 'true'; load.hidden = true;
        loading.textContent = `Ready to play and seek · ${(blob.size/1048576).toFixed(1)} MB loaded`;
      } catch (error) {
        if (error.name !== 'AbortError') {loading.textContent = `Could not load clip: ${error.message}. Retry or download the MP4.`; load.disabled = false;}
      } finally {pendingLoads.delete(controller);}
    });
    div.append(node('h4', m.label), video, load, loading, node('p', m.quality, 'muted'),
      node('p', `${m.source_task_passed ? 'Task passed' : 'Task FAILED'} · ${m.mac_playback_verified ? 'Mac playback verified' : 'Mac playback pending'} · ${m.source_hashes_verified ? 'Replay source hashes verified' : 'Legacy replay: no original source-hash verification'}`, 'muted'));
    const links = node('div', undefined, 'links'); const download = link('Download MP4', m.url); download.download = `${c.id}-${m.directory.split('/').at(-1)}.mp4`;
    links.append(download, link('Render manifest', m.manifest));
    const presentation = m.presentation;
    const status = presentation?.status || 'candidate';
    const labels = {accepted_working_presentation: 'Accepted working presentation',
      reviewed_failure_diagnostic: 'Reviewed failure diagnostic — NOT a successful cycle',
      candidate: 'Presentation candidate — acceptance pending'};
    const acceptance = node('p', labels[status] || labels.candidate, 'presentation-status');
    acceptance.dataset.status = status; div.append(acceptance);
    if (presentation?.record) {
      div.append(node('p', `${presentation.frames} encoded frames · ${presentation.inspected_sheets} inspected sheets / ${presentation.sampled_frames} sampled frames. Combined technical, systematic visual and natural Mac-playback review; not exhaustive manual native-frame inspection.`, 'muted'));
      for (const [label, key] of [['Acceptance record', 'record'], ['Visual observations', 'visual_review'], ['Temporal report', 'temporal_report']]) {
        links.append(link(label, presentation.links[presentation[key]]));
      }
    }
    div.append(links); return div;
  });
  content.append(details(`Recorded videos (${clips.length})`, clips.length ? clips : [node('p', 'Four-view capture and multi-angle edit pending. No generated stand-in is shown.', 'muted')]));
  const versions = c.versions.map(v => {
    const div = node('div', undefined, 'version');
    div.append(node('strong', `${v.version} · ${v.status === 'failed_feasibility' ? 'failed feasibility' : 'single feasibility pass'}`),
      node('p', `${v.scene_load_verified ? 'Scene load verified' : 'Scene load unverified'} · ${v.declared_outcome_verified ? 'Declared outcome reproduced' : 'Declared outcome NOT reproduced'}`, v.declared_outcome_verified ? 'muted' : 'version-warning'),
      node('p', v.hardware_revision || 'Original connection geometry', 'muted'), node('code', `/workspace/${v.path}`), node('code', `cd /workspace\n${v.run_command}`));
    const links = node('div', undefined, 'links');
    for (const name of ['manifest', 'config', 'results']) links.append(link(name, v.links[name]));
    v.links.reload_reports.forEach((p, i) => links.append(link(`reload ${i + 1}`, p)));
    div.append(links); return div;
  });
  content.append(details(`Preserved environments (${versions.length})`, versions));
  if (c.mechanical_link) content.append(link('Recorded-motion mechanical screen', c.mechanical_link));
  article.append(content); return article;
}
async function main() {
  const response = await fetch('data.json', {cache:'no-store'});
  if (!response.ok) throw Error(`Evidence request failed (${response.status})`);
  const data = await response.json();
  const currentTrials = data.designs.reduce((n,c)=>n+(c.current_benchmark?.admissible_manipulation_trials || 0),0);
  for (const [value, label] of [[data.designs.length, 'combinations'], [currentTrials, 'current valid trials'], [data.randomized_trials, 'historical randomized trials'], [data.preserved_versions, 'saved versions'], [`${data.loaded_versions}/${data.preserved_versions}`, 'verified scene loads']]) {
    const total = node('div', undefined, 'total'); total.append(node('strong', value), node('span', label)); $('#totals').append(total);
  }
  $('#benchmark-source').href = localURL(data.sources.benchmark);
  if (Object.keys(data.physical_challenges || {}).length) {
    const section = node('section'); section.id = 'physical-challenges';
    section.append(node('h2','Physical latch and open-tool challenges'),
      node('p','Separate diagnostic campaigns test retained pulling and open-command transport. A completed campaign can contain failed diagnostic gates; none of these cases adds to randomized reliability.'),
      node('p','An open command is not always a release: the specialized C tool can retain housing contact through its guide geometry. Read the matched hold/move results and the original failures together.', 'muted'));
    for (const [name,report] of Object.entries(data.physical_challenges)) {
      const passed = Object.values(report.cases).filter(c=>c.diagnostic_passed).length;
      section.append(node('p',`${name}: ${passed}/${Object.keys(report.cases).length} diagnostic cases passed. Overall diagnostic ${report.passed ? 'PASS' : 'FAIL — counterevidence preserved'}.`),
        link('Verified '+name+' evidence',data.sources[name+'-verification']));
    }
    const links=node('div',undefined,'links');
    for (const [label,key] of [['Original challenge results','physical_challenge_results001.md'],
      ['Matched hold/move interpretation','matched_release_results001.md'],['Research source review','source_review001.md']]) {
      if (data.sources[key]) links.append(link(label,data.sources[key]));
    }
    section.append(links); $('#recommendation').after(section);
  }
  if (data.comparison && data.nominal_cable_forces) {
    $('#recommendation').hidden = false;
    $('#recommendation-source').href = localURL(data.sources['current_design_comparison.md']);
    for (const ranked of data.comparison.rankings_by_reliability_weight['45']) {
      const force = data.nominal_cable_forces.designs[ranked.design];
      const row = node('tr'); row.dataset.design = ranked.design;
      for (const value of [ranked.design, ranked.total.toFixed(2),
        force.peak_tension.force_n.toFixed(2)+' N', force.plug_joint_peak_tension_n.toFixed(2)+' N',
        (1000*force.exposure_above_n['5.0'].total_duration_s).toFixed(2)+' ms']) row.append(node('td',value));
      $('#recommendation-comparison').append(row);
    }
    for (const [label,key] of [['Scoring evidence','current-comparison'], ['Nominal force evidence','nominal-cable-forces'],
      ['Force method and limitations','cable_momentum_measurement.md'], ['Parts, dimensions and cost gaps','buildability_and_bom.md']]) {
      $('#recommendation-links').append(link(label,data.sources[key]));
    }
  }
  for (const c of data.designs) {
    const b=c.current_benchmark; const row=node('tr'); row.dataset.design=c.id;
    const current=c.current ? `${c.current.version} · ${c.current.passed ? 'nominal pass' : 'FAILED'}` : 'Unverified';
    const unavailable=c.current?.passed ? 'Pending cohort' : 'Not eligible';
    const interval=b?.wilson_95_interval ? b.wilson_95_interval.map(v=>(100*v).toFixed(1)+'%').join('–') : '—';
    for (const value of [c.id,current,b ? `${b.complete_cycles} / ${b.admissible_manipulation_trials}` : unavailable,
      b ? `${b.complete_cycles} / ${b.planned}` : '—',b ? b.fixture_failures : '—',interval,
      b?.mean_successful_cycle_s != null ? b.mean_successful_cycle_s.toFixed(2)+' s' : '—']) row.append(node('td',value));
    $('#current-comparison').append(row);
  }
  for (const c of data.designs) {
    const b = c.benchmark; const row = node('tr'); const name = node('td');
    const anchor = node('a', `${c.id[0]}/${c.id[1]}`); anchor.href = `#design-${c.id}`;
    anchor.addEventListener('click', () => {reset();}); name.append(anchor); row.append(name);
    const interval = b ? b.wilson_95_interval.map(v => `${(v*100).toFixed(1)}%`).join('–') : '—';
    const mass = c.mechanical ? `${c.mechanical.total_modeled_mass_kg.toFixed(3)} kg${b ? '' : ' · ' + c.mechanical_version + ' failed'}` : 'Pending';
    const current = c.current ? `${c.current.version} · ${c.current.passed ? 'nominal pass' : 'FAILED'}` : 'Unverified';
    for (const value of [current, shortVersion(b), count(b), interval, b ? `${b.mean_successful_cycle_s.toFixed(2)} s` : '—', c.neighbors ? `${c.neighbors.clearance_passes} / ${c.neighbors.cases}` : 'Not tested', mass]) row.append(node('td', value));
    $('#comparison').append(row);
  }
  const filters = ['#robot-filter', '#tool-filter', '#outcome-filter'];
  function render() {
    pendingLoads.forEach(controller => controller.abort()); pendingLoads.clear();
    playbackURLs.forEach(url => URL.revokeObjectURL(url)); playbackURLs.clear();
    const [robot, tool, outcome] = filters.map(id => $(id).value);
    const filtered = data.designs.filter(c => (robot === 'all' || c.id[0] === robot) && (tool === 'all' || c.id[1] === tool) && (outcome === 'all' || (outcome === 'tested' ? Boolean(c.benchmark) : outcome === 'passed' ? c.current?.passed === true : c.current ? c.current.passed === false : !c.benchmark)));
    $('#designs').replaceChildren(...filtered.map(card)); $('#result-count').textContent = `${filtered.length} of ${data.designs.length} combinations`;
    $('#empty').hidden = filtered.length !== 0;
  }
  function reset() { filters.forEach(id => {$(id).value = 'all';}); render(); }
  filters.forEach(id => $(id).addEventListener('change', render)); $('#reset-filters').addEventListener('click', reset);
  for (const [name, path] of Object.entries(data.sources)) $('#evidence-links').append(link(name.replaceAll('_', ' '), path));
  $('#evidence-links').append(link('Download all displayed data', 'data.json'), link('Artifact hashes', 'manifest.json'));
  $('#snapshot').textContent = `Snapshot ${data.generated_utc} · ${data.reproduced_outcomes}/${data.preserved_versions} declared outcomes reproduced. Not a live job monitor.`;
  render();
}
main().catch(error => {$('#error').hidden = false; $('#error').textContent = `Gallery could not load its evidence: ${error.message}`;});

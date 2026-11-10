const $ = id => document.getElementById(id);
let properties = [];
let selectedProperty = null;
let currentLanguage = 'english';

const money = n => 'PHP ' + Number(n).toLocaleString('en-PH');
const taglish = text => /\b(po|ba|yung|magkano|pwede|gusto|ako|kami|ko|naman|lang|saan|paano|mahal|mura|may|meron|kaya|sa|ng|ang)\b/i.test(text);
const say = (en, tl) => currentLanguage === 'taglish' ? tl : en;

async function api(url, options) {
  const res = await fetch(url, options);
  const data = await res.json();
  if (!res.ok) throw Error(data.error || 'Request failed');
  return data;
}

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function addMessage(message, who) {
  const node = element('div', message, 'message ' + who);
  if (who === 'bot' && !$('interactive').hidden) $('interactive').before(node);
  else $('messages').append(node);
  $('messages').scrollTop = $('messages').scrollHeight;
}

function clearPanel() {
  $('interactive').replaceChildren();
  $('interactive').hidden = true;
}

function panel(title, note) {
  clearPanel();
  $('interactive').hidden = false;
  $('interactive').append(element('p', title, 'panel-title'));
  if (note) $('interactive').append(element('p', note, 'panel-note'));
  requestAnimationFrame(() => $('interactive').scrollIntoView({block:'nearest', behavior:'smooth'}));
  return $('interactive');
}

function actionButton(label, handler, primary = false) {
  const btn = element('button', label, primary ? 'primary' : '');
  btn.type = 'button';
  btn.addEventListener('click', handler);
  return btn;
}

function propertyList(items, title) {
  const root = panel(title, say('Select a property to view details.', 'Pili po ng property para makita ang details.'));
  const grid = element('div', undefined, 'option-list');
  for (const property of items) {
    const btn = element('button', undefined, 'option');
    btn.type = 'button';
    btn.append(element('strong', property.name), element('small', property.location));
    const unit = property.matching_units?.[0] || (property.matching_units ? null : property.units?.[0]);
    btn.append(element('small', unit
      ? `${unit.size} - ${money(unit.tcp_php)} (2025 listed)`
      : say('No listed unit within budget / price not documented', 'Walang documented listing na pasok sa budget / walang price data')));
    btn.addEventListener('click', () => {
      selectedProperty = property.id;
      showDetails(property);
    });
    grid.append(btn);
  }
  root.append(grid);
}

function showDetails(p) {
  const root = panel(p.name, p.location);
  const details = element('div', undefined, 'panel-note');
  const units = p.units?.length
    ? `${p.units.length} listings in historical price list. Price range: ${money(Math.min(...p.units.map(u => u.tcp_php)))} to ${money(Math.max(...p.units.map(u => u.tcp_php)))}\n` + p.units.slice(0, 8).map(u => `${u.size}: ${money(u.tcp_php)} (${u.status_as_listed || "historical"})`).join('\n')
    : say('Prices not verified', 'Hindi pa verified ang prices');
  details.style.whiteSpace = 'pre-wrap';
  details.textContent = `${say('Unit sizes and historical prices', 'Unit sizes at historical prices')}:\n${units}\n\n` +
    `${say('Availability', 'Availability')}: ${say('Unverified', 'Hindi pa confirmed')}\n` +
    `${say('Payment terms', 'Payment terms')}: ${(p.payment_terms || []).join('; ')}\n` +
    `${say('Contact', 'Contact')}: ${p.contact?.phone || say('Agent contact not verified', 'Hindi pa verified ang agent contact')}`;
  root.append(details);
  const actions = element('div', undefined, 'actions');
  const maps = element('a', say('View on Google Maps', 'Tingnan sa Google Maps'));
  maps.href = p.directions_url;
  maps.target = '_blank';
  maps.rel = 'noopener noreferrer';
  actions.append(maps, actionButton(say('Request viewing', 'Mag-request ng viewing'), () => viewingForm(p.id), true));
  root.append(actions);
}

function viewingForm(propertyId) {
  const root = panel(say('Viewing request', 'Viewing request'), say(
    'Choose a preferred date and time. This is not a confirmed booking.',
    'Pili po ng preferred date at time. Hindi pa ito confirmed booking.'
  ));
  const form = element('form', undefined, 'inline-form');
  const fields = [
    ['property_id', say('Property', 'Property'), 'select'],
    ['date', say('Preferred date', 'Preferred date'), 'date'],
    ['time', say('Preferred time', 'Preferred time'), 'select'],
    ['name', say('Your name', 'Pangalan'), 'text'],
    ['contact', say('Contact information', 'Contact information'), 'text']
  ];
  for (const [key, label, type] of fields) {
    const wrap = element('label', label);
    const control = document.createElement(type === 'select' ? 'select' : 'input');
    control.name = key;
    control.required = true;
    if (type !== 'select') control.type = type;
    if (key === 'date') {
      const now = new Date();
      control.min = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
    }
    if (key === 'property_id') {
      for (const p of properties) {
        const opt = element('option', p.name);
        opt.value = p.id;
        control.append(opt);
      }
      if (propertyId) control.value = propertyId;
    }
    if (key === 'time') {
      for (const time of ['09:00', '10:00', '11:00', '13:00', '14:00', '15:00']) {
        const opt = element('option', time);
        opt.value = time;
        control.append(opt);
      }
    }
    wrap.append(control);
    form.append(wrap);
  }
  const submit = element('button', say('Prepare viewing request', 'I-prepare ang viewing request'), 'primary');
  submit.type = 'submit';
  form.append(submit);
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(form).entries());
    try {
      const result = await api('/api/viewing', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(values)
      });
      addMessage(say(result.message, 'Na-prepare ang viewing request, pero hindi pa ito sent o confirmed. Contact the agent po para ma-confirm.'), 'bot');
      clearPanel();
    } catch (error) { addMessage(error.message, 'bot'); }
  });
  root.append(form);
}

function budgetForm() {
  const root = panel(say('Find properties for your budget', 'Hanap ng property ayon sa budget'),
    say('Enter your maximum total property price in pesos.', 'Ilagay po ang maximum total property price in pesos.'));
  const form = element('form', undefined, 'inline-form');
  const wrap = element('label', say('Maximum budget (PHP)', 'Maximum budget (PHP)'));
  const input = document.createElement('input');
  input.type = 'number'; input.min = '100000'; input.step = '100000'; input.required = true; input.placeholder = '6000000';
  wrap.append(input);
  const submit = element('button', say('Find matches', 'Hanapin ang pasok sa budget'), 'primary');
  submit.type = 'submit';
  form.append(wrap, submit);
  form.addEventListener('submit', event => {
    event.preventDefault();
    sendMessage(say(`My budget is PHP ${input.value}. Recommend properties.`, `Budget ko po ay PHP ${input.value}. Ano ang pasok na property?`));
  });
  root.append(form);
}

function suggestedOptions(query) {
  const lower = query.trim().toLowerCase();
  const box = $('suggestions');
  box.replaceChildren();
  if (!lower) { box.hidden = true; return; }
  const matching = properties.filter(p =>
    p.name.toLowerCase().includes(lower) ||
    p.location.toLowerCase().includes(lower) ||
    (lower.length >= 3 && p.type.toLowerCase().includes(lower))
  );
  const options = matching.length ? matching : properties;
  for (const property of options.slice(0, 5)) {
    const btn = element('button', undefined, 'suggestion');
    btn.type = 'button';
    btn.append(element('strong', property.name), element('small', property.location));
    btn.addEventListener('click', () => {
      box.hidden = true;
      selectedProperty = property.id;
      sendMessage(say(`Tell me about ${property.name}.`, `Pwede po bang malaman ang details ng ${property.name}?`), property.id);
    });
    box.append(btn);
  }
  box.hidden = false;
}

async function sendMessage(message, propertyId = null) {
  currentLanguage = taglish(message) ? 'taglish' : 'english';
  addMessage(message, 'user');
  $('message').value = '';
  $('suggestions').hidden = true;
  clearPanel();
  try {
    const response = await api('/api/chat', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message, property_id: propertyId || selectedProperty})
    });
    addMessage(response.reply, 'bot');
    if (response.action === 'viewing') viewingForm(response.selected_property || selectedProperty);
    else if (response.action === 'budget') {
      if (response.budget) propertyList(response.properties, say('Budget-based property options', 'Mga property na pwede sa budget'));
      else budgetForm();
    } else if (response.selected_property && ['pricing', 'payment', 'contact', 'location', 'availability'].includes(response.action)) {
      const selected = properties.find(p => p.id === response.selected_property);
      if (selected) showDetails(selected);
    } else if (response.action === 'discover' || response.action === 'pricing') {
      propertyList(properties, say('Our properties', 'Mga property na ino-offer'));
    } else if (response.action === 'location' || response.action === 'contact') {
      propertyList(properties, say('Choose a property', 'Pili po ng property'));
    }
  } catch (error) {
    addMessage(say('The backend is unavailable: ', 'Hindi ma-contact ang backend: ') + error.message, 'bot');
  }
}

$('message').addEventListener('input', e => suggestedOptions(e.target.value));
$('message').addEventListener('keydown', e => { if (e.key === 'Escape') $('suggestions').hidden = true; });
$('chatForm').addEventListener('submit', event => {
  event.preventDefault();
  const message = $('message').value.trim();
  if (message) sendMessage(message);
});
(async function init() {
  try { properties = await api('/api/properties'); }
  catch (error) { addMessage('Unable to load property information. Start the Flask backend.', 'bot'); }
})();

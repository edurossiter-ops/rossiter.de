/* Newsletter — handler autônomo para as páginas do blog (mesmo endpoint HubSpot da home) */
(function () {
  var nf = document.getElementById('newsForm');
  if (!nf) return;
  nf.addEventListener('submit', async function (e) {
    e.preventDefault();
    var input = nf.querySelector('input[type=email]'), btn = nf.querySelector('button');
    var email = input ? input.value.trim() : ''; if (!email) return;
    if (btn) { btn.disabled = true; btn.textContent = '...'; }
    var endpoint = 'https://forms-eu1.hsforms.com/submissions/v3/integration/submit/148665264/71c42ccf-ac88-49a2-bff9-fe9dca2b2c8d';
    try {
      var res = await fetch(endpoint, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fields: [{ objectTypeId: '0-1', name: 'email', value: email }], context: { pageUri: location.href, pageName: document.title } })
      });
      nf.innerHTML = res.ok
        ? '<p style="color:var(--sky);font-size:.95rem">Pronto. Você está inscrito.</p>'
        : '<p style="color:var(--sky);font-size:.95rem">Recebido. Se não confirmar, escreva para eduardo@rossiter.de.</p>';
    } catch (_) {
      nf.innerHTML = '<p style="color:var(--sky);font-size:.95rem">Recebido. Se não confirmar, escreva para eduardo@rossiter.de.</p>';
    }
  });
})();

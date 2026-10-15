(() => {
  const languageButton = document.getElementById('language-toggle');
  const menuButton = document.getElementById('menu-toggle');
  const navigation = document.getElementById('navigation');
  const status = document.getElementById('copy-status');
  let language = 'en';
  function setLanguage(next) {
    language = next === 'zh' ? 'zh' : 'en';
    document.documentElement.lang = language === 'zh' ? 'zh-CN' : 'en';
    document.querySelectorAll('[data-en][data-zh]').forEach(element => {
      element.textContent = element.dataset[language];
    });
    languageButton.dataset.lang = language;
    languageButton.setAttribute('aria-label', language === 'zh' ? 'Switch to English' : '切换为中文');
    document.title = language === 'zh' ? 'Lutong Wen | 商业分析与运营作品集' : 'Lutong Wen | Business Analytics & Operations';
    status.textContent = '';
    try { localStorage.setItem('lutong-portfolio-language', language); } catch {}
  }
  let saved; try { saved = localStorage.getItem('lutong-portfolio-language'); } catch {}
  setLanguage(new URLSearchParams(location.search).get('lang') || saved || 'en');
  languageButton.addEventListener('click', () => setLanguage(language === 'en' ? 'zh' : 'en'));
  menuButton.addEventListener('click', () => {
    const open = navigation.classList.toggle('open');
    menuButton.setAttribute('aria-expanded', String(open));
  });
  navigation.querySelectorAll('a').forEach(link => link.addEventListener('click', () => {
    navigation.classList.remove('open'); menuButton.setAttribute('aria-expanded', 'false');
  }));
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && navigation.classList.contains('open')) {
      navigation.classList.remove('open'); menuButton.setAttribute('aria-expanded', 'false');menuButton.focus();
    }
  });
  document.getElementById('copy-email').addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText('wenlutong199@gmail.com');
      status.textContent = language === 'zh' ? '邮箱已复制' : 'Email address copied';
    } catch {
      status.textContent = language === 'zh' ? '请手动复制：wenlutong199@gmail.com' : 'Please copy: wenlutong199@gmail.com';
    }
  });
})();

(() => {
  const topNavigation = document.querySelector('.research-jumps');
  const rail = document.querySelector('[data-research-rail]');
  const story = document.querySelector('.research-story');
  const sections = Array.from(document.querySelectorAll('.research-section[id]'));

  if (!topNavigation || !rail || !story || sections.length === 0) return;

  const links = Array.from(rail.querySelectorAll('a[href^="#"]'));
  let frame = 0;

  const setVisible = (visible) => {
    rail.classList.toggle('is-visible', visible);
    rail.setAttribute('aria-hidden', String(!visible));
    links.forEach((link) => {
      link.tabIndex = visible ? 0 : -1;
    });
  };

  const update = () => {
    frame = 0;

    const header = document.querySelector('body > header');
    const headerBottom = header ? header.getBoundingClientRect().bottom : 0;
    const activationLine = headerBottom + Math.min(window.innerHeight * 0.28, 200);
    const topRect = topNavigation.getBoundingClientRect();
    const storyRect = story.getBoundingClientRect();
    const footer = document.querySelector('body > footer');
    const footerClear = !footer || footer.getBoundingClientRect().top > window.innerHeight - 24;
    const visible = topRect.bottom <= headerBottom + 12
      && storyRect.bottom > activationLine
      && footerClear;

    setVisible(visible);

    let activeSection = sections[0];
    sections.forEach((section) => {
      if (section.getBoundingClientRect().top <= activationLine) activeSection = section;
    });

    links.forEach((link) => {
      const isActive = link.hash === `#${activeSection.id}`;
      link.classList.toggle('is-active', isActive);
      if (isActive) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
  };

  const scheduleUpdate = () => {
    if (frame) return;
    frame = window.requestAnimationFrame(update);
  };

  rail.hidden = false;
  setVisible(false);
  update();

  window.addEventListener('scroll', scheduleUpdate, { passive: true });
  window.addEventListener('resize', scheduleUpdate, { passive: true });
  window.addEventListener('pageshow', scheduleUpdate);
})();

(() => {
  const className = 'teiban-example-highlight';
  function update() {
    for (const element of document.querySelectorAll(`[data-teiban-target], .${className}`)) {
      const matches = element.tagName === 'H2' &&
        element.getAttribute('data-teiban-target') === 'notice' &&
        element.textContent.trim() === '定番サンプル';
      if (element.classList.contains(className) !== matches) {
        element.classList.toggle(className, matches);
      }
    }
  }
  update();
  new MutationObserver(update).observe(document.documentElement, {
    childList: true,
    subtree: true,
    characterData: true,
    attributes: true,
    attributeFilter: ['data-teiban-target', 'class']
  });
})();

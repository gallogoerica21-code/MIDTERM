(() => {
  const initialRevision = document.body.dataset.liveRevision;
  const revisionUrl = document.body.dataset.liveRevisionUrl;

  if (!initialRevision || !revisionUrl) {
    return;
  }

  let revision = initialRevision;
  let requestPending = false;

  window.setInterval(async () => {
    if (document.hidden || requestPending) {
      return;
    }

    requestPending = true;
    try {
      const response = await fetch(revisionUrl, { cache: "no-store" });
      if (!response.ok) {
        return;
      }

      const result = await response.json();
      if (result.revision !== revision) {
        window.location.reload();
        return;
      }
      revision = result.revision;
    } catch (error) {
      console.error("Could not check for live inventory updates.", error);
    } finally {
      requestPending = false;
    }
  }, 5000);
})();

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'GET_TABS') {
      const queryOptions = message.currentWindow ? { currentWindow: true } : {};
      chrome.tabs.query(queryOptions, (tabs) => {
        const tabData = tabs.map(tab => ({
          id: tab.id,
          title: tab.title,
          url: tab.url,
          favIconUrl: tab.favIconUrl
        }));
        sendResponse(tabData);
      });
      return true; // Indicate async response
    }
  });
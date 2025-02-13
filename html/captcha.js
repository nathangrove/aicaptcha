// Throttle function to limit the rate at which a function can fire
function throttle(func, limit) {
  let lastFunc;
  let lastRan;
  return function() {
    const context = this;
    const args = arguments;
    if (!lastRan) {
      func.apply(context, args);
      lastRan = Date.now();
    } else {
      clearTimeout(lastFunc);
      lastFunc = setTimeout(function() {
        if ((Date.now() - lastRan) >= limit) {
          func.apply(context, args);
          lastRan = Date.now();
        }
      }, limit - (Date.now() - lastRan));
    }
  };
}

const interactionData = {
    mouseMovements: [],
    keyPresses: [],
    scrollEvents: [],
    formInteractions: [],
    touchEvents: [],
    mouseClicks: []
  };
  
  // Capture mouse movements with throttling
  document.addEventListener('mousemove', throttle((event) => {
    console.log('Mouse move:', event.clientX, event.clientY);
    interactionData.mouseMovements.push({
      x: event.clientX,
      y: event.clientY,
      time: Date.now(),
    });
  }, 100)); // Adjust the limit (in milliseconds) as needed
  
  // Capture key presses
  document.addEventListener('keydown', (event) => {
    console.log('Key press:', event.key);
    interactionData.keyPresses.push({
      key: event.key,
      time: Date.now(),
    });
  });
  
  // Capture scroll events
  document.addEventListener('scroll', () => {
    console.log('Scroll:', document.documentElement.scrollTop);
    interactionData.scrollEvents.push({
      scrollTop: document.documentElement.scrollTop,
      time: Date.now(),
    });
  });
  
  // Capture form interactions
  document.querySelectorAll('form').forEach((form) => {
    form.addEventListener('submit', (event) => {
      const formData = new FormData(form);
      formData.forEach((value, key) => {
        console.log('Form interaction:', key, value);
        interactionData.formInteractions.push({
          field: key,
          value: value.toString(),
          time: Date.now(),
        });
      });
    });
  });
  
  // Capture touch events
  document.addEventListener('touchstart', (event) => {
    const touch = event.touches[0];
    console.log('Touch start:', touch.clientX, touch.clientY);
    interactionData.touchEvents.push({
      type: 'start',
      x: touch.clientX,
      y: touch.clientY,
      time: Date.now(),
      force: touch.force,
    });
  });
  
  document.addEventListener('touchmove', throttle((event) => {
    const touch = event.touches[0];
    console.log('Touch move:', touch.clientX, touch.clientY);
    interactionData.touchEvents.push({
      type: 'move',
      x: touch.clientX,
      y: touch.clientY,
      time: Date.now(),
      force: touch.force,
    });
  }, 100)); // Adjust the limit (in milliseconds) as needed
  
  document.addEventListener('touchend', (event) => {
    const touch = event.changedTouches[0];
    console.log('Touch end:', touch.clientX, touch.clientY);
    interactionData.touchEvents.push({
      type: 'end',
      x: touch.clientX,
      y: touch.clientY,
      time: Date.now(),
      force: touch.force,
    });
  });

  // Capture mouse clicks
  document.addEventListener('mousedown', (event) => {
    console.log('Mouse down:', event.clientX, event.clientY);
    interactionData.mouseClicks.push({
      type: 'down',
      x: event.clientX,
      y: event.clientY,
      time: Date.now()
    });
  });

  document.addEventListener('mouseup', (event) => {
    console.log('Mouse up:', event.clientX, event.clientY);
    interactionData.mouseClicks.push({
      type: 'up',
      x: event.clientX,
      y: event.clientY,
      time: Date.now()
    });
  });
  
  const loadTimestamp = Date.now();
  // Function to send data to the server
  async function sendDataToServer(event) {
    event.preventDefault(); // Prevent the default form submission
    console.log('Sending data:', interactionData);
    const b64Data = btoa(JSON.stringify({
      interactions: interactionData,
      duration: Date.now() - loadTimestamp,
      userAgent: navigator.userAgent,
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight,
      },
      loadTimestamp,
    }));
    const response = await fetch('/api/challenge', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ data: b64Data }),
    });
  
    const result = await response.json();
    return result.token;
  }
  
  // Example usage: send data when a button is clicked
  document.getElementById('submitButton').addEventListener('click', sendDataToServer);
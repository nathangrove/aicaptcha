class AICaptcha {
  constructor(config = {
    autoIntercept: false,
    publicKey: ''
  }) {
    this.config = config;
    this.interactionData = {
      mouseMovements: [],
      keyPresses: [],
      scrollEvents: [],
      formInteractions: [],
      touchEvents: [],
      mouseClicks: []
    };
    this.loadTimestamp = Date.now();
    this.captureInteractions();
    if (config.autoIntercept) {
      this.interceptFormSubmissions();
    }
  }

  throttle(func, limit) {
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

  captureInteractions() {
    // Capture mouse movements with throttling
    document.addEventListener('mousemove', this.throttle((event) => {
      this.interactionData.mouseMovements.push({
        x: event.clientX,
        y: event.clientY,
        time: Date.now(),
      });
    }, 100)); // Adjust the limit (in milliseconds) as needed

    // Capture key presses
    document.addEventListener('keydown', (event) => {
      this.interactionData.keyPresses.push({
        key: event.key,
        time: Date.now(),
      });
    });

    // Capture scroll events
    document.addEventListener('scroll', () => {
      this.interactionData.scrollEvents.push({
        scrollTop: document.documentElement.scrollTop,
        time: Date.now(),
      });
    });

    // Capture form interactions
    document.querySelectorAll('form').forEach((form) => {
      form.addEventListener('submit', (event) => {
        const formData = new FormData(form);
        formData.forEach((value, key) => {
          this.interactionData.formInteractions.push({
            field: key,
            time: Date.now(),
          });
        });
      });
    });

    // Capture touch events
    document.addEventListener('touchstart', (event) => {
      const touch = event.touches[0];
      this.interactionData.touchEvents.push({
        type: 'start',
        x: touch.clientX,
        y: touch.clientY,
        time: Date.now(),
        force: touch.force,
      });
    });

    document.addEventListener('touchmove', this.throttle((event) => {
      const touch = event.touches[0];
      this.interactionData.touchEvents.push({
        type: 'move',
        x: touch.clientX,
        y: touch.clientY,
        time: Date.now(),
        force: touch.force,
      });
    }, 100)); // Adjust the limit (in milliseconds) as needed

    document.addEventListener('touchend', (event) => {
      const touch = event.changedTouches[0];
      this.interactionData.touchEvents.push({
        type: 'end',
        x: touch.clientX,
        y: touch.clientY,
        time: Date.now(),
        force: touch.force,
      });
    });

    // Capture mouse clicks
    document.addEventListener('mousedown', (event) => {
      this.interactionData.mouseClicks.push({
        type: 'down',
        x: event.clientX,
        y: event.clientY,
        time: Date.now()
      });
    });

    document.addEventListener('mouseup', (event) => {
      this.interactionData.mouseClicks.push({
        type: 'up',
        x: event.clientX,
        y: event.clientY,
        time: Date.now()
      });
    });
  }

  async sendDataToServer() {
    const data = {
      interactions: this.interactionData,
      duration: Date.now() - this.loadTimestamp,
      userAgent: navigator.userAgent,
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight,
      },
      loadTimestamp: this.loadTimestamp,
    };
    const response = await fetch('/api/challenge', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.config.publicKey}`
      },
      body: JSON.stringify({data}),
    });

    const result = await response.json();
    console.log('captcha response:', result);
    return result.token;
  }

  interceptFormSubmissions() {
    document.querySelectorAll('form').forEach((form) => {
      form.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent the form from submitting immediately
        const token = await this.sendDataToServer();
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'captcha_token';
        input.value = token;
        form.appendChild(input);
        form.submit();
      });
    });
  }

  async executeAsync() {
    const token = await this.sendDataToServer();
    return token;
  }
}

/*
// Initialize the CAPTCHA library
const aiCaptcha = new AICaptcha({
  autoIntercept: false, // Set to true to automatically intercept form submissions and append result to them
});
*/
// Example usage of the AICaptcha class manually
// const aiCaptcha = new AICaptcha({ publicKey: 'your_public_key_here' });
// aiCaptcha.executeAsync().then(token => {
//   console.log('Captcha token:', token);
// });

// Automatically intercept form submissions
// const aiCaptcha = new AICaptcha({
//   autoIntercept: true,
//   publicKey: 'your_public_key_here'
// });
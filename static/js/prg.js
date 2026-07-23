let currentStep = 1;
    const totalSteps = 4;

    function nextStep(from) {
      if (!validateStep(from)) return;
      setStep(from + 1);
    }
    function prevStep(from) { setStep(from - 1); }

    function setStep(n) {
      document.querySelectorAll('.form-step').forEach(s => s.classList.remove('active'));
      document.getElementById('step-' + n).classList.add('active');
      document.querySelectorAll('.step').forEach((s, i) => {
        s.classList.toggle('active', i < n);
        s.classList.toggle('done', i < n - 1);
      });
      currentStep = n;
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function validateStep(n) {
      const step = document.getElementById('step-' + n);
      const inputs = step.querySelectorAll('[required]');
      let valid = true;
      inputs.forEach(input => {
        input.classList.remove('error');
        if (!input.value.trim()) { input.classList.add('error'); valid = false; }
      });
      if (!valid) { const first = step.querySelector('.error'); if (first) first.focus(); }
      return valid;
    }

    function previewPhoto(input) {
      if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = e => {
          const preview = document.getElementById('photoPreview');
          preview.src = e.target.result;
          preview.style.display = 'block';
          document.getElementById('fileUpload').style.display = 'none';
        };
        reader.readAsDataURL(input.files[0]);
      }
    }

    document.getElementById('pat_password').addEventListener('input', function() {
      const val = this.value;
      const fill = document.getElementById('pwFill');
      const label = document.getElementById('pwLabel');
      let score = 0;
      if (val.length >= 8) score++;
      if (/[A-Z]/.test(val)) score++;
      if (/[0-9]/.test(val)) score++;
      if (/[^A-Za-z0-9]/.test(val)) score++;
      const levels = ['', 'Weak', 'Fair', 'Good', 'Strong'];
      const colors = ['', '#ef4444', '#f59e0b', '#3b82f6', '#10b981'];
      fill.style.width = (score * 25) + '%';
      fill.style.background = colors[score];
      label.textContent = levels[score] || '';
      label.style.color = colors[score];
    });

    document.getElementById('patientForm').addEventListener('submit', function() {
      document.getElementById('submitBtn').style.display = 'none';
      document.getElementById('formLoader').style.display = 'flex';
    });

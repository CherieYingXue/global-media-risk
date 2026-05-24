(function () {
  const toast = document.getElementById('toast');
  const btnRefresh = document.getElementById('btnRefresh');
  const btnGenerate = document.getElementById('btnGenerate');

  function showToast(msg, duration) {
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.remove('hidden');
    clearTimeout(showToast._timer);
    showToast._timer = setTimeout(() => toast.classList.add('hidden'), duration || 4000);
  }

  async function pollReportStatus() {
    const maxAttempts = 90;
    for (let i = 0; i < maxAttempts; i++) {
      await new Promise((r) => setTimeout(r, 2000));
      try {
        const res = await fetch('/api/report/status', { cache: 'no-store' });
        if (!res.ok) continue;
        const st = await res.json();
        if (st.message) showToast(st.message, 5000);

        if (st.status === 'done') {
          showToast(`报告已生成，共 ${st.items} 条风险信号`);
          setTimeout(() => location.reload(), 1200);
          return true;
        }
        if (st.status === 'error') {
          showToast('生成失败: ' + (st.error || '未知错误'));
          return false;
        }
      } catch (_) {
        /* 轮询偶发失败继续重试 */
      }
    }
    showToast('生成时间较长，请稍后刷新页面查看结果');
    return false;
  }

  async function generateReport() {
    const btn = btnRefresh || btnGenerate;
    if (btn && btn.disabled) return;

    showToast('正在启动采集分析…');
    if (btn) btn.disabled = true;

    try {
      const res = await fetch('/api/report/refresh?_=' + Date.now(), {
        method: 'GET',
        cache: 'no-store',
      });
      if (!res.ok) {
        const hint = res.status === 502
          ? '公网隧道已断开，请运行 deploy.bat 或换用同一 WiFi 局域网链接'
          : '请重试';
        showToast('请求失败 (' + res.status + ')，' + hint);
        return;
      }
      const data = await res.json();
      if (!data.ok && data.status !== 'running') {
        showToast('启动失败: ' + (data.error || data.message || '未知错误'));
        return;
      }
      showToast(data.message || '正在采集，预计 1–2 分钟…', 6000);
      await pollReportStatus();
    } catch (e) {
      showToast('网络错误，请检查连接后重试');
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  if (btnRefresh) btnRefresh.addEventListener('click', generateReport);
  if (btnGenerate) btnGenerate.addEventListener('click', generateReport);

  document.querySelectorAll('.filter-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      const filter = btn.dataset.filter;
      document.querySelectorAll('.risk-card').forEach((card) => {
        if (filter === 'all') {
          card.classList.remove('hidden');
        } else {
          const labels = card.dataset.labels || '';
          card.classList.toggle('hidden', !labels.includes(filter));
        }
      });
    });
  });
})();

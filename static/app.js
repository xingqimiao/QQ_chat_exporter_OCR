// static/app.js
document.addEventListener('DOMContentLoaded', () => {
    // 【优化】将滚动容器也获取到
    const resultsContainer = document.querySelector('.results-container');
    const resultsPre = document.getElementById('results');
    
    // ... 其他所有DOM元素获取保持不变 ...
    const panels = document.querySelectorAll('.panel');
    const steps = document.querySelectorAll('.step');
    const newConfigBtn = document.getElementById('newConfigBtn');
    const loadConfigBtn = document.getElementById('loadConfigBtn');
    const regionConfigPanel = document.getElementById('region-config-panel');
    const speakerConfigPanel = document.getElementById('speaker-config-panel');
    const configRegionBtn = document.getElementById('configRegionBtn');
    const s1NameInput = document.getElementById('s1_name_input');
    const s2NameInput = document.getElementById('s2_name_input');
    const saveAndStartBtn = document.getElementById('saveAndStartBtn');
    const downloadBtn = document.getElementById('downloadBtn');

    let eventSource;

    function goToStep(stepNumber) {
        panels.forEach(p => p.classList.remove('active'));
        steps.forEach(s => s.classList.remove('active'));
        document.getElementById(`panel-${stepNumber}`)?.classList.add('active');
        document.getElementById(`step-${stepNumber}`)?.classList.add('active');
    }

    // ... newConfigBtn, loadConfigBtn, configRegionBtn, saveAndStartBtn 的事件监听器都保持不变 ...
    newConfigBtn.addEventListener('click', () => {
        goToStep(2);
    });

    if (loadConfigBtn) {
        loadConfigBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/load-config');
                const data = await response.json();
                if (data.status === 'success') {
                    alert('上次配置已成功加载！即将开始抓取。');
                    goToStep(3);
                    startScrapingProcess();
                } else {
                    alert('加载配置失败: ' + data.message);
                }
            } catch (error) {
                alert('请求加载配置失败: ' + error);
            }
        });
    }
    
    configRegionBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/configure', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ step: 'region' })
            });
            const data = await response.json();
            if (data.status === 'success') {
                regionConfigPanel.style.display = 'none';
                speakerConfigPanel.style.display = 'block';
            } else {
                alert('区域配置失败: ' + data.message);
            }
        } catch (error) {
            alert('请求配置区域失败: ' + error);
        }
    });

    saveAndStartBtn.addEventListener('click', async () => {
        const configData = {
            step: 'names_and_colors',
            s1_name: s1NameInput.value || '左侧发言人',
            s2_name: s2NameInput.value || '右侧发言人',
        };

        try {
            const response = await fetch('/configure', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(configData)
            });
            const data = await response.json();
            if (data.status === 'success') {
                alert('新配置已保存！即将开始抓取。');
                goToStep(3);
                startScrapingProcess();
            } else {
                alert('配置保存失败: ' + data.message);
            }
        } catch (error) {
            alert('请求保存配置失败: ' + error);
        }
    });

    function startScrapingProcess() {
        resultsPre.textContent = '正在连接服务器，准备开始抓取...\n';
        eventSource = new EventSource('/start-scrape');
        
        eventSource.onmessage = function(event) {
            const message = JSON.parse(event.data);
            const line = document.createElement('div');
            
            if (message.speaker === '系统消息') {
                line.textContent = message.text;
                line.style.textAlign = 'center';
                line.style.color = '#888';
                line.style.fontSize = '0.8em';
                line.style.margin = '10px 0';
            } else {
                line.textContent = `${message.speaker}：${message.text}`;
            }
            resultsPre.appendChild(line);
            
            // 【画龙点睛之笔】让容器滚动到底部！
            resultsContainer.scrollTop = resultsContainer.scrollHeight;
        };

        eventSource.addEventListener('finished', function(event) {
            resultsPre.innerHTML += `\n<div style="text-align:center; color:green; font-weight:bold;">--- ${event.data} ---</div>\n`;
            eventSource.close();
            goToStep(4);
            resultsContainer.scrollTop = resultsContainer.scrollHeight;
        });

        eventSource.onerror = function(error) {
            resultsPre.innerHTML += '\n<div style="text-align:center; color:red; font-weight:bold;">--- 连接错误或中断 ---</div>\n';
            eventSource.close();
            goToStep(4);
        };
    }

    downloadBtn.addEventListener('click', () => {
        window.location.href = '/download';
    });
});
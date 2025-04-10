// Format tool outputs based on type
export function formatToolOutput(content, toolName) {
    // Try to parse JSON if the content looks like JSON
    let jsonContent;
    try {
        if (content.trim().startsWith('{') || content.trim().startsWith('[')) {
            jsonContent = JSON.parse(content);
        }
    } catch (e) {
        // Not JSON, continue with string content
    }

    // Tool-specific formatting
    switch (toolName) {
        case 'analyze_image':
            return formatImageAnalysis(jsonContent || content);
        case 'python_repl':
            return formatPythonOutput(content);
        case 'get_resource_usage':
            return formatSystemMetrics(jsonContent || content);
        case 'list_running_processes':
            return formatProcessList(jsonContent || content);
        default:
            return formatGenericOutput(content);
    }
}

function formatImageAnalysis(content) {
    if (typeof content === 'object') {
        let html = '<div class="tool-output image-analysis">';
        
        // Add original image if path is present
        if (content.file) {
            html += `<img src="/workspace/${content.file}" class="chat-image" alt="Analyzed Image"/>`;
        }
        
        // Format analysis results
        if (content.labels) {
            html += '<h4>Detected Labels:</h4><ul>';
            content.labels.forEach(label => {
                html += `<li>${label.name} (${label.confidence}%)</li>`;
            });
            html += '</ul>';
        }
        
        // Add other analysis sections...
        
        return html + '</div>';
    }
    return formatGenericOutput(content);
}

function formatPythonOutput(content) {
    let html = '<div class="python-output">';
    
    // Handle plot outputs
    if (content.includes('plot has been generated')) {
        const plotMatch = content.match(/saved as '(.+?)'/);
        if (plotMatch) {
            html += `<div class="plot-container">
                <img src="/workspace/${plotMatch[1]}" class="chat-image" alt="Python Plot"/>
            </div>`;
        }
    }
    
    // Format code output
    html += `<pre><code class="language-python">${escapeHtml(content)}</code></pre>`;
    
    return html + '</div>';
}

function formatSystemMetrics(content) {
    if (typeof content === 'object') {
        let html = '<div class="tool-output system-metrics">';
        Object.entries(content).forEach(([key, value]) => {
            html += `<div class="metric-row">
                <span class="metric-key">${key}:</span>
                <span class="metric-value">${value}</span>
            </div>`;
        });
        return html + '</div>';
    }
    return formatGenericOutput(content);
}

function formatProcessList(content) {
    if (Array.isArray(content)) {
        let html = `<div class="tool-output process-list">
            <table class="markdown-table">
                <thead>
                    <tr>
                        <th>PID</th>
                        <th>Name</th>
                        <th>CPU %</th>
                        <th>Memory %</th>
                    </tr>
                </thead>
                <tbody>`;
        
        content.forEach(process => {
            html += `<tr>
                <td>${process.PID}</td>
                <td>${process.Name}</td>
                <td>${process.CPU}</td>
                <td>${process.Memory}</td>
            </tr>`;
        });
        
        return html + '</tbody></table></div>';
    }
    return formatGenericOutput(content);
}

function formatGenericOutput(content) {
    // Handle markdown-style code blocks
    content = content.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
        return `<pre><code class="language-${lang}">${escapeHtml(code)}</code></pre>`;
    });
    
    // Handle inline code
    content = content.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Handle images
    content = content.replace(/!\[(.*?)\]\((.*?)\)/g, '<img src="$2" alt="$1" class="chat-image"/>');
    
    return `<div class="tool-output">${content}</div>`;
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Export other utility functions
export function formatTimestamp(date) {
    return new Intl.DateTimeFormat('default', {
        hour: 'numeric',
        minute: 'numeric',
        second: 'numeric'
    }).format(date);
}

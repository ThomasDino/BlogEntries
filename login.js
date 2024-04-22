function loadDoc(url, cFunction) {
    const xhttp = new XMLHttpRequest();
    xhttp.onload = function() {
        if (xhttp.status === 200) {
            cFunction(this);
        } else {
            console.error('Error fetching data');
        }
    };
    xhttp.open("GET", url, true);
    xhttp.send();
}

function login() {
    let txtEmail = document.getElementById("txtEmail");
    let txtPassword = document.getElementById("txtPassword");

    if (txtEmail.value == '' || txtPassword.value == '') {
        alert("Email and Password can not be blank.");
        return;
    }
    let URL = "/login?email=" + txtEmail.value + "&password=" + txtPassword.value;

    let chkRemember = document.getElementById("chkRemember");
    if (chkRemember.checked) {
        URL += "&remember=yes";
    } else {
        URL += "&remember=no";
    }
    loadDoc(URL, login_response);
}

function login_response(response) {
    let data = JSON.parse(response.responseText);
    let result = data["result"];
    if (result != "OK") {
        alert(result);
    }
    else {
        window.location.replace("/account.html");
    }
}

function loadEntries() {
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            try {
                var responseData = JSON.parse(this.responseText);
                var list = document.getElementById('entriesList');
                list.innerHTML = '';
                responseData.entries.forEach(function(entry) {
                    var item = document.createElement('li');
                    item.textContent = `${entry.date} - ${entry.title}: ${entry.text}`;
                    if (responseData.logged_in) {
                        var deleteBtn = document.createElement('button');
                        deleteBtn.textContent = 'Delete';
                        deleteBtn.onclick = function() { deleteEntry(entry.post_id); };
                        item.appendChild(deleteBtn);
                    }
                    list.appendChild(item);
                });
            } catch (error) {
                console.error('Error parsing JSON:', error);
            }
        }
    };
    xhttp.open("GET", "/entries", true);
    xhttp.send();
}



window.onload = loadEntries;



function addBlogEntry() {
    let title = document.getElementById('title').value
    let text = document.getElementById('text').value

    if(!title && !text){
        alert('Please put a title and body to post! You can\'t just post blank thoughts......')
        return
    }

    let xhttp = new XMLHttpRequest()
    xhttp.onload = function(){
        if (xhttp.status === 200){
            const response = JSON.parse(xhttp.responseText)

            const titleElement = document.createElement('p')
            titleElement.textContent = response.title

            const postElement = document.createElement('p')
            postElement.textContent = response.text

            const dashboard = document.getElementById('dashboard')
            dashboard.appendChild(titleElement)
            dashboard.appendChild(postElement)

            alert('Post uploaded successfully!');
            renderPost();
        } else {
            console.log('Error uploading post!');
            alert('Error uploading post!');
        }
    };

    xhttp.open('POST', '/add_entry', true)
    const formData = new FormData()
    formData.append('title', title)
    formData.append('text', text)

    xhttp.send(formData)
}



function deleteEntry(postId) {
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            console.log('Entry deleted successfully');
            loadEntries();
        }
    };
    xhttp.open("POST", "/delete_entry", true);
    xhttp.setRequestHeader("Content-Type", "application/json");
    xhttp.send(JSON.stringify({ post_id: postId }));
}

function register() {
    const email = document.getElementById('regEmail').value;
    const username = document.getElementById('regUsername').value;
    const password = document.getElementById('regPassword').value;

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/register', true);
    xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                alert('Registration successful!');
            } else {
                alert('Registration failed: ' + xhr.responseText);
            }
        }
    };
    xhr.send(JSON.stringify({
        email: email,
        username: username,
        password: password
    }));
}

function deleteAccount() {
    if (confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
        var xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function() {
            if (this.readyState === 4) {
                if (this.status === 200) {
                    alert('Account deleted successfully.');
                    window.location.href = '/login';
                } else {
                    alert('Failed to delete account: ' + this.responseText);
                }
            }
        };
        xhttp.open("POST", "/delete_account", true);
        xhttp.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
        xhttp.send();
    }
}










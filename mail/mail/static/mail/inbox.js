document.addEventListener('DOMContentLoaded', function () {

    // Use buttons to toggle between views
    document.querySelector('#inbox').addEventListener('click', () => load_mailbox('inbox'));
    document.querySelector('#sent').addEventListener('click', () => load_mailbox('sent'));
    document.querySelector('#archive').addEventListener('click', () => load_mailbox('archive'));
    document.querySelector('#compose').addEventListener('click', compose_email);
    document.querySelector('#compose-form').onsubmit = send_email;
    // By default, load the inbox
    load_mailbox('inbox');
});

function compose_email() {

    // Show compose view and hide other views
    document.querySelector('#emails-view').style.display = 'none';
    document.querySelector('#compose-view').style.display = 'block';
    document.querySelector('#single-email-view').style.display = 'none';
    document.querySelectorAll("button").forEach(button => button.classList.remove("selected"));
    document.querySelector(`#compose`).classList.add("selected");
    document.querySelector('#compose-recipients').value = '';
    document.querySelector('#compose-subject').value = '';
    document.querySelector('#compose-body').value = '';
}

function reply_email(email) {
    compose_email();
    document.querySelector('#compose-recipients').value = email["sender"];
    document.querySelector('#compose-subject').value =
        email["subject"].slice(0, 4) === "Re: " ? email["subject"] : "Re: " + email["subject"];
    const pre_body_text = `------ On ${email['timestamp']} ${email["sender"]} wrote:`;
    document.querySelector('#compose-body').value = pre_body_text + email["body"].replace(/^/gm, "\t");
}

function archive_email(email_id, to_archive) {
    fetch(`/emails/${email_id}`, {
        method: 'PUT',
        body: JSON.stringify({
            archived: to_archive
        })
    }).then(() => load_mailbox("inbox"));

}




function load_email(email_id, origin_mailbox) {
    document.querySelector('#emails-view').style.display = 'none';
    document.querySelector('#compose-view').style.display = 'none';
    document.querySelector('#single-email-view').style.display = 'block';
    document.querySelector('#single-email-content').innerHTML = '';
    document.querySelector('#single-email-back-section').innerHTML = '';

    fetch(`/emails/${email_id}`)
        .then(response => response.json())
        .then(email => {
            if ("error" in email) { console.log(email) }
            ["subject", "timestamp", "sender", "recipients", "body"].forEach(email_element => {
                const row = document.createElement('div');
                row.classList.add("row", 'border', 'border-info', "d-flex", "align-items-center", "justify-content-between");
                if (email_element === "subject") {
                    const col_subject = document.createElement('div');
                    col_subject.classList.add("col-10", "d-flex", "align-items-center");
                    col_subject.innerHTML = `<p class="text-justify pt-3">${email_element.toUpperCase()} : ${email[email_element]}</p>`;
                    row.append(col_subject);

                    const col_reply_archive = document.createElement('div');
                    col_reply_archive.classList.add("col-2", "d-flex", "align-items-center", "justify-content-end");
                    col_reply_archive.id = "archive-reply-button";
                    const data_for_potential_buttons_to_add = [
                        ["Reply", () => reply_email(email)],
                        [email["archived"] ? "Unarchive" : "Archive",
                        () => archive_email(email_id, !email["archived"])]
                    ];

                    (origin_mailbox === "sent" ?
                        data_for_potential_buttons_to_add.slice(0, 1) : data_for_potential_buttons_to_add)
                        .forEach(text_function => {
                            const text = text_function[0];
                            const callback_func = text_function[1];
                            const button = document.createElement("button");
                            button.classList.add("btn", "btn-info", "m-2");
                            button.innerHTML = text;
                            button.addEventListener('click', callback_func);
                            col_reply_archive.append(button);
                        });
                    row.append(col_reply_archive);

                } else if (email_element === "body") {
                    row.innerHTML = `<p class="text-justify pt-2" style="padding-bottom: 300px">${email[email_element]}</p>`;
                }
                else {
                    row.innerHTML = `<p class="text-justify pt-3">${email_element.toUpperCase()} : ${email[email_element]}</p>`;
                }

                document.querySelector("#single-email-content").append(row);
            });
            const back_button_col_div = document.createElement('div');
            back_button_col_div.classList.add("m-3", "d-flex", "align-items-center", "justify-content-center",);
            back_button_col_div.innerHTML =
                `<p class="btn btn-danger px-5">Back to ${origin_mailbox.charAt(0).toUpperCase() + origin_mailbox.slice(1)}</p>`;
            back_button_col_div.addEventListener('click', () => load_mailbox(origin_mailbox));
            document.querySelector("#single-email-back-section").append(back_button_col_div);


        })
        .catch(error => console.log(error));


    fetch(`/emails/${email_id}`, {
        method: 'PUT',
        body: JSON.stringify({
            read: true
        })
    }).then();

}


function load_mailbox(mailbox) {

    // Show the mailbox and hide other views
    document.querySelector('#emails-view').style.display = 'block';
    document.querySelector('#compose-view').style.display = 'none';
    document.querySelector('#single-email-view').style.display = 'none';
    document.querySelectorAll("button").forEach(button => button.classList.remove("selected"));
    document.querySelector(`#${mailbox}`).classList.add("selected");
    document.querySelector('#emails-view').innerHTML = `<h3>${mailbox.charAt(0).toUpperCase() + mailbox.slice(1)}</h3>`;


    fetch(`/emails/${mailbox}`)
        .then(response => response.json())
        .then(emails => {
            const sections_to_show = [['sender', 5], ['subject', 3], ['timestamp', 4]];
            const artificial_first_email = { 'sender': 'Sender', 'subject': 'Subject', 'timestamp': 'Date and time', 'read': true };
            emails = [artificial_first_email, ...emails];
            emails.forEach(email => {
                const row_div_element = document.createElement('div');
                row_div_element.classList.add("row", "border", "text-center", email.read ? "bg-dark" : "bg-secondary");
                sections_to_show.forEach(
                    section => {
                        const section_name = section[0];
                        const section_size = section[1];
                        const div_section = document.createElement('div');
                        div_section.classList.add(`col-${section_size}`);
                        div_section.innerHTML = `<p class="pt-3">${email[section_name]}</p>`;
                        row_div_element.append(div_section);

                    });
                if (email !== artificial_first_email) {
                    row_div_element.addEventListener('click', () => load_email(email["id"], mailbox));
                }

                document.querySelector('#emails-view').append(row_div_element);
            })
        })
        .catch(error => console.log(error));
}

function send_email() {
    const recipients = document.querySelector('#compose-recipients').value;
    const subject = document.querySelector('#compose-subject').value;
    const body = document.querySelector('#compose-body').value;

    fetch('/emails', {
        method: 'POST',
        body: JSON.stringify({
            recipients: recipients,
            subject: subject,
            body: body
        })
    })
        .then(response => response.json())
        .then(result => {
            if ("message" in result) {
                load_mailbox('sent');
            }

            if ("error" in result) {
                document.querySelector('#to-text-error-message').innerHTML = result['error']
            }
        })
        .catch(error => {
            console.log(error);
        });
    return false;
}

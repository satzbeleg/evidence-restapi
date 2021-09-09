SELECT auth.add_new_email_account('nobody@example.com', 'supersecret');
SELECT auth.check_verification_token(auth.issue_verification_token(auth.lookup_userid_by_email('nobody@example.com')));

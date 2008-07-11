<?xml version="1.0" encoding="utf-8" ?>
<emails>
% for item in c.emailtemplates:
<email id="${item.id}" key="${item.key}">
    <subject>${item.subject}</subject>
    <from_email>${item.from_email}</from_email>
    <from_name>${item.from_name}</from_name>
    <to>${item.to}</to>
    <template><![CDATA[${item.template}]]></template>
</email>
% endfor
</emails>

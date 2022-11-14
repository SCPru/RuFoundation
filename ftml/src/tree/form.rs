use super::AttributeMap;
use std::borrow::Cow;

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq)]
#[serde(rename_all = "kebab-case")]
pub struct Form<'t> {
    pub target: Cow<'t, str>,
    pub inputs: Vec<FormInput<'t>>,
}

impl Form<'_> {
    pub fn to_owned(&self) -> Form<'static> {
        Form {
            target: Cow::Owned(self.target.to_string()),
            inputs: self.inputs.iter().map(|input| input.to_owned()).collect(),
        }
    }
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq)]
#[serde(rename_all = "kebab-case")]
pub struct FormInput<'t> {
    pub attributes: AttributeMap<'t>,
}

impl FormInput<'_> {
    pub fn to_owned(&self) -> FormInput<'static> {
        FormInput {
            attributes: self.attributes.to_owned(),
        }
    }
}
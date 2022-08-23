/*
 * data/page_ref.rs
 *
 * ftml - Library to parse Wikidot text
 * Copyright (C) 2019-2022 Wikijump Team
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

use ref_map::*;
use std::borrow::Cow;
use std::fmt::{self, Display};

/// Represents a reference to a page on the wiki, as used by include notation.
#[derive(Serialize, Deserialize, Debug, Clone, Hash, PartialEq, Eq)]
#[serde(rename_all = "kebab-case")]
pub struct PageRef<'t> {
    pub site: Option<Cow<'t, str>>,
    pub category: Cow<'t, str>,
    pub name: Cow<'t, str>,
}

impl<'t> PageRef<'t> {
    #[inline]
    pub fn new3<S1, S2, S3>(site: S1, category: S2, name: S3) -> Self
    where
        S1: Into<Cow<'t, str>>,
        S2: Into<Cow<'t, str>>,
        S3: Into<Cow<'t, str>>,
    {
        PageRef {
            site: Some(site.into()),
            category: category.into(),
            name: name.into(),
        }
    }

    #[inline]
    pub fn new2<S1, S2>(category: S1, name: S2) -> Self
    where
        S1: Into<Cow<'t, str>>,
        S2: Into<Cow<'t, str>>,
    {
        PageRef {
            site: None,
            category: category.into(),
            name: name.into(),
        }
    }

    #[inline]
    pub fn new1<S>(name: S) -> Self
    where
        S: Into<Cow<'t, str>>,
    {
        PageRef {
            site: None,
            category: Cow::from("_default"),
            name: name.into(),
        }
    }

    #[inline]
    pub fn site(&self) -> Option<&str> {
        self.site.ref_map(|s| s.as_ref())
    }

    #[inline]
    pub fn category(&self) -> &str {
        self.category.as_ref()
    }

    #[inline]
    pub fn name(&self) -> &str {
        self.name.as_ref()
    }

    #[inline]
    pub fn fields(&self) -> (Option<&str>, &str, &str) {
        (self.site(), self.category(), self.name())
    }

    /// Like `fields()`, but uses the passed in value as the current site for local references.
    pub fn fields_or<'a>(&'a self, current_site: &'a str) -> (&'a str, &'a str, &'a str) {
        (self.site().unwrap_or(current_site), self.category(), self.name())
    }

    pub fn parse(s: &str) -> Result<PageRef<'t>, PageRefParseError> {
        let s = s.trim();
        if s.is_empty() {
            return Err(PageRefParseError);
        }

        let result = match s.find(':') {
            // Off-site page, e.g. ":scp-wiki:something"
            Some(0) => {
                // Find the second colon
                let idx = match s[1..].find(':') {
                    // Empty site name, e.g. "::something"
                    // or no second colon, e.g. ":something"
                    Some(0) | None => return Err(PageRefParseError),

                    // Slice off the rest
                    Some(idx) => idx + 1,
                };

                // Get site and page slices
                let site = s[1..idx].trim();
                let page_raw = s[(idx+1)..].trim();
                
                let (category, name) = match page_raw.find(':') {
                    Some(idx) => {
                        let category = &page_raw[..idx];
                        let name = &page_raw[(idx+1)..];
                        (category, name)
                    }
                    _ => ("_default", page_raw)
                };

                PageRef::new3(site.to_owned(), category.to_owned(), name.to_owned())
            }

            // On-site page, e.g. "component:thing"
            Some(idx) => {
                let category = &s[..idx];
                let name = &s[(idx+1)..];
                PageRef::new2(category.to_owned(), name.to_owned())
            }

            // On-site page, with no category, e.g. "page"
            None => PageRef::new1(s.to_owned()),
        };

        Ok(result)
    }

    pub fn to_owned(&self) -> PageRef<'static> {
        macro_rules! owned {
            ($value:expr) => {
                Cow::Owned($value.as_ref().to_owned())
            };
        }

        let site = self.site.ref_map(|value| owned!(value));
        let category = owned!(self.category);
        let name = owned!(self.name);

        PageRef { site, category, name }
    }
}

impl Display for PageRef<'_> {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        if let Some(site) = self.site() {
            write!(f, ":{}:", &site)?;
        }

        if self.category() != "_default" {
            write!(f, "{}:", &self.category())?;
        }

        write!(f, "{}", &self.name())
    }
}

#[derive(Debug, PartialEq, Eq)]
pub struct PageRefParseError;

#[test]
fn page_ref() {
    macro_rules! test {
        ($input:expr $(,)?) => {
            test!($input => None)
        };

        ($input:expr, $expected:expr $(,)?) => {
            test!($input => Some($expected))
        };

        ($input:expr => $expected:expr) => {{
            let actual = PageRef::parse($input);
            let expected = $expected.ok_or(PageRefParseError);

            println!("Input: {:?}", $input);
            println!("Output: {:?}", actual);
            println!();

            assert_eq!(actual, expected, "Actual parse results don't match expected");
            if let Ok(expected) = expected {
                assert_eq!(expected.to_string(), $input, "Encoded PageRef does not match expected");
            }
        }};
    }

    test!("");
    test!(":page");
    test!("::page");
    test!("page", PageRef::new1("page"));
    test!("component:page", PageRef::new2("component", "page"));
    test!(
        "deleted:secret:fragment:page",
        PageRef::new2("deleted", "secret:fragment:page"),
    );
    test!(":scp-wiki:page", PageRef::new3("scp-wiki", "_default", "page"));
    test!(
        ":scp-wiki:component:page",
        PageRef::new3("scp-wiki", "component", "page"),
    );
    test!(
        ":scp-wiki:deleted:secret:fragment:page",
        PageRef::new3("scp-wiki", "deleted", "secret:fragment:page"),
    );
}

#[cfg(test)]
mod prop {
    use super::*;
    use proptest::prelude::*;

    proptest! {
        #![proptest_config(ProptestConfig::with_cases(4096))]

        #[test]
        fn page_ref_prop(s in r"[a-zA-Z_:.]*") {
            let _ = PageRef::parse(&s);
        }
    }
}

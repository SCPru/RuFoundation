/*
 * preproc/typography.rs
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

//! Perform Wikidot's typographical modifications.
//! For full information, see the original source file:
//! https://github.com/gabrys/wikidot/blob/master/lib/Text_Wiki/Text/Wiki/Parse/Default/Typography.php
//!
//! The transformations performed here are listed:
//! * `` .. '' to fancy double quotes
//! * ` .. ' to fancy single quotes
//! * ,, .. '' to fancy lowered double quotes
//! * ... to an ellipsis
//!
//! Em dash conversion was originally implemented here, however
//! it was moved to the parser to prevent typography from converting
//! the `--` in `[!--` and `--]` into em dashes.

use regex::Regex;

lazy_static! {
    // ‘ - LEFT SINGLE QUOTATION MARK
    // ’ - RIGHT SINGLE QUOTATION MARK
    static ref SINGLE_QUOTES: Replacer = Replacer::RegexSurround {
        regex: Regex::new(r"`(.*?)'").unwrap(),
        begin: "\u{2018}",
        end: "\u{2019}",
    };

    // “ - LEFT DOUBLE QUOTATION MARK
    // ” - RIGHT DOUBLE QUOTATION MARK
    static ref DOUBLE_QUOTES: Replacer = Replacer::RegexSurround {
        regex: Regex::new(r"``(.*?)''").unwrap(),
        begin: "\u{201c}",
        end: "\u{201d}",
    };

    // „ - DOUBLE LOW-9 QUOTATION MARK
    static ref LOW_DOUBLE_QUOTES: Replacer = Replacer::RegexSurround {
        regex: Regex::new(r",,(.*?)''").unwrap(),
        begin: "\u{201e}",
        end: "\u{201d}",
    };

    // … - HORIZONTAL ELLIPSIS
    /*static ref ELLIPSIS: Replacer = Replacer::RegexReplace {
        regex: Regex::new(r"(?:\.\.\.|\. \. \.)").unwrap(),
        replacement: "\u{2026}",
    };*/
}

/// Helper struct to easily perform string replacements.
#[derive(Debug)]
pub enum Replacer {
    /// Replaces any text matching the regular expression with the static string.
    /// The entire match is used, any capture groups are ignored.
    RegexReplace {
        regex: Regex,
        replacement: &'static str,
    },

    /// Takes text matching the regular expression, and replaces the exterior.
    ///
    /// The regular expression must return the content to be preserved in
    /// capture group 1, and surrounds it with the `begin` and `end` strings.
    ///
    /// For instance, say:
    /// * `regex` matched `[% (.+) %]`
    /// * `begin` was `<(`
    /// * `end` was `)>`
    ///
    /// Then input string `[% wikidork %]` would become `<(wikidork)>`.
    RegexSurround {
        regex: Regex,
        begin: &'static str,
        end: &'static str,
    },
}

impl Replacer {
    fn replace(&self, text: &mut String, buffer: &mut String) {
        use self::Replacer::*;

        match *self {
            RegexReplace {
                ref regex,
                replacement,
            } => {
                debug!(
                    "Running regex regular expression replacement (pattern {}, replacement {})",
                    regex.as_str(),
                    replacement,
                );

                while let Some(capture) = regex.captures(text) {
                    let range = {
                        let mtch = capture
                            .get(0)
                            .expect("Regular expression lacks a full match");

                        mtch.start()..mtch.end()
                    };

                    text.replace_range(range, replacement);
                }
            }
            RegexSurround {
                ref regex,
                begin,
                end,
            } => {
                debug!(
                    "Running surround regular expression capture replacement (pattern {}, begin {}, end {})",
                    regex.as_str(),
                    begin,
                    end,
                );

                while let Some(capture) = regex.captures(text) {
                    let mtch = capture
                        .get(1)
                        .expect("Regular expression lacks a content group");

                    let range = {
                        let mtch = capture
                            .get(0)
                            .expect("Regular expression lacks a full match");

                        mtch.start()..mtch.end()
                    };

                    buffer.clear();
                    buffer.push_str(begin);
                    buffer.push_str(mtch.as_str());
                    buffer.push_str(end);

                    text.replace_range(range, buffer);
                }
            }
        }
    }
}

pub fn substitute(text: &mut String) {
    let mut buffer = String::new();
    info!("Performing typography substitutions");

    macro_rules! replace {
        ($replacer:expr) => {
            $replacer.replace(text, &mut buffer)
        };
    }

    // Quotes
    replace!(DOUBLE_QUOTES);
    replace!(LOW_DOUBLE_QUOTES);
    replace!(SINGLE_QUOTES);

    // Miscellaneous
    //replace!(ELLIPSIS);
}
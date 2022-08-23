/*
 * includes/test.rs
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

use super::{include, DebugIncluder, PageRef};
use crate::settings::{WikitextMode, WikitextSettings};

#[test]
fn includes() {
    let settings = WikitextSettings::from_mode(WikitextMode::Page);

    macro_rules! test {
        ($text:expr, $expected:expr $(,)?) => {{
            let mut text = str!($text);
            let result = include(&mut text, &settings, DebugIncluder, || panic!());
            let (output, actual) = result.expect("Fetching pages failed");
            let expected = $expected;

            println!("Input:  '{}'", $text);
            println!("Output: '{}'", &output);
            println!("Pages (actual):   {:?}", &actual);
            println!("Pages (expected): {:?}", &expected);
            println!();

            assert_eq!(
                &actual, &expected,
                "Actual pages to include doesn't match expected"
            );
        }};
    }

    // Valid cases

    test!("", vec![]);
    test!("[[include-messy page]]", vec![PageRef::new1("page")]);
    test!("[[include-messy page ]]", vec![PageRef::new1("page")]);
    test!("[[include-messy page ]]", vec![PageRef::new1("page")]);
    test!("[[ include-messy page ]]", vec![PageRef::new1("page")]);

    test!("[[include-messy PAGE]]", vec![PageRef::new1("PAGE")]);
    test!("[[include-messy PAGE ]]", vec![PageRef::new1("PAGE")]);
    test!("[[include-messy PAGE ]]", vec![PageRef::new1("PAGE")]);
    test!("[[ include-messy PAGE ]]", vec![PageRef::new1("PAGE")]);

    // Arguments
    test!(
        "[[include-messy apple a =1]]",
        vec![PageRef::new1("apple")],
    );
    test!(
        "[[include-messy apple a= 1]]",
        vec![PageRef::new1("apple")],
    );
    test!(
        "[[include-messy apple a = 1]]",
        vec![PageRef::new1("apple")],
    );
    test!(
        "[[include-messy apple a = 1 ]]",
        vec![PageRef::new1("apple")],
    );
    test!(
        "[[include-messy apple  a = 1 ]]",
        vec![PageRef::new1("apple")],
    );

    test!(
        "[[include-messy banana a=1]]",
        vec![PageRef::new1("banana")],
    );
    test!(
        "[[include-messy banana a=1|]]",
        vec![PageRef::new1("banana")],
    );
    test!(
        "[[include-messy banana a=1 |]]",
        vec![PageRef::new1("banana")],
    );
    test!(
        "[[include-messy banana |a=1]]",
        vec![PageRef::new1("banana")],
    );
    test!(
        "[[include-messy banana | a=1]]",
        vec![PageRef::new1("banana")],
    );
    test!(
        "[[include-messy banana |a=1|]]",
        vec![PageRef::new1("banana")],
    );
    test!(
        "[[include-messy banana | a=1|]]",
        vec![PageRef::new1("banana")],
    );
    test!(
        "[[include-messy banana |a=1 |]]",
        vec![PageRef::new1("banana")],
    );
    test!(
        "[[include-messy banana | a=1 |]]",
        vec![PageRef::new1("banana")],
    );

    test!(
        "[[include-messy cherry a=1|b=2]]",
        vec![PageRef::new1("cherry")],
    );
    test!(
        "[[include-messy cherry a=1|b=2|]]",
        vec![PageRef::new1("cherry")],
    );
    test!(
        "[[include-messy cherry a=1 |b=2 |]]",
        vec![PageRef::new1("cherry")],
    );
    test!(
        "[[include-messy cherry |a=1|b=2]]",
        vec![PageRef::new1("cherry")],
    );
    test!(
        "[[include-messy cherry | a=1| b=2]]",
        vec![PageRef::new1("cherry")],
    );
    test!(
        "[[include-messy cherry |a=1|b=2|]]",
        vec![PageRef::new1("cherry")],
    );
    test!(
        "[[include-messy cherry | a=1| b=2|]]",
        vec![PageRef::new1("cherry")],
    );
    test!(
        "[[include-messy cherry |a=1 |b=2 |]]",
        vec![PageRef::new1("cherry")],
    );
    test!(
        "[[include-messy cherry | a=1 | b=2 |]]",
        vec![PageRef::new1("cherry")],
    );

    test!(
        "[[include-messy durian a=1|b=2|C=**]]",
        vec![PageRef::new1("durian")],
    );
    test!(
        "[[include-messy durian a=1|b=2|C=**|]]",
        vec![PageRef::new1("durian")],
    );
    test!(
        "[[include-messy durian a=1 |b=2 |C=** |]]",
        vec![PageRef::new1("durian")],
    );
    test!(
        "[[include-messy durian |a=1|b=2|C=**]]",
        vec![PageRef::new1("durian")],
    );
    test!(
        "[[include-messy durian | a=1| b=2| C=**]]",
        vec![PageRef::new1("durian")],
    );
    test!(
        "[[include-messy durian |a=1|b=2|C=**|]]",
        vec![PageRef::new1("durian")],
    );
    test!(
        "[[include-messy durian | a=1| b=2| C=**|]]",
        vec![PageRef::new1("durian")],
    );
    test!(
        "[[include-messy durian |a=1 |b=2 |C=** |]]",
        vec![PageRef::new1("durian")],
    );
    test!(
        "[[include-messy durian | a=1 | b=2 | C=** ]]",
        vec![PageRef::new1("durian")],
    );

    // Off-site includes
    test!(
        "[[include-messy component:my-thing]]",
        vec![PageRef::new1("component:my-thing")],
    );
    test!(
        "[[include-messy :scp-wiki:main]]",
        vec![PageRef::new3("scp-wiki", "_default", "main")],
    );
    test!(
        "[[include-messy :scp-wiki:component:my-thing]]",
        vec![PageRef::new3("scp-wiki", "_default", "component:my-thing")],
    );
    test!(
        "[[include-messy :scp-wiki:deleted:protected:component:magic]]",
        vec![PageRef::new3(
            "scp-wiki",
            "_default",
            "deleted:protected:component:magic"
        )],
    );

    // Multiple include-messys
    test!(
        "A\n[[include-messy B]]\nC\n[[include-messy D]]\nE\n[[include-messy F]]\nG",
        vec![
            PageRef::new1("B"),
            PageRef::new1("D"),
            PageRef::new1("F"),
        ],
    );
    test!(
        "[[include-messy my-page]]\n[[include-messy :scp-wiki:theme:black-highlighter-theme]]\n",
        vec![
            PageRef::new1("my-page"),
            PageRef::new3("scp-wiki", "_default", "theme:black-highlighter-theme"),
        ],
    );

    // Multi-line includes
    test!("[[include-messy page\n]]", vec![PageRef::new1("page")]);
    test!(
        "[[include-messy component:multi-line | contents= \nSome content here \nMore stuff]]",
        vec![PageRef::new1("component:multi-line")],
    );
    test!(
        "[[include-messy component:multi-line argument=x | contents= \nSome content here \nMore stuff \n|]]",
        vec![PageRef::new1("component:multi-line")],
    );
    test!(
        "[[include-messy component:multi-line | contents= \nSome content here\nMore stuff\n]]",
        vec![PageRef::new1("component:multi-line")],
    );
    test!(
        "[[include-messy component:multi-line | contents=\nSome content here\nMore stuff\n]]",
        vec![PageRef::new1("component:multi-line")],
    );
    test!(
        "My wonderful page!\n\n[[include-messy component:info-ayers\n\tlang=en |\n\tpage=scp-xxxx |\n\tauthorPage=http://scpwiki.com/main |\n\tcomments=\n**SCP-XXXX:** My amazing skip \n**Author:** [[*user Username]] \n]]",
        vec![PageRef::new1("component:info-ayers")],
    );
    test!(
        "My other wonderful page!\n\n[[include-messy component:info-ayers\n\t|lang=en\n\t|page=scp-xxxx\n\t|authorPage=http://scpwiki.com/main\n\t|comments=\n**SCP-XXXX:** My amazing skip \n**Author:** [[*user Username]] \n]]",
        vec![PageRef::new1("component:info-ayers")],
    );

    // Invalid cases

    test!("other text", vec![]);
    test!("include-messy]]", vec![]);
    test!("[[include-messy", vec![]);
    test!("[[include-messy]]", vec![]);
    test!("[[include-messy ]]", vec![]);
    test!("[[ include-messy]]", vec![]);

    test!(
        "[[include-messy component:multi-line | contents= \nSome content here \nMore stuff",
        vec![],
    );
}
